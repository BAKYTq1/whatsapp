"""
WhatsApp-бот для учеников.

Что делает:
  1. По расписанию (по умолчанию Пн/Ср/Пт в 19:00) пишет каждому ученику
     из students.csv: «Привет, <имя>! Как идёт учёба? ...»
  2. Когда ученик отвечает — пересылает ответ учителю в WhatsApp.
  3. Если задан GEMINI_API_KEY (бесплатно) или ANTHROPIC_API_KEY — сам отвечает
     ученикам на вопросы по курсу и присылает учителю копию вопроса и ответа.

Работает через официальный WhatsApp Cloud API (Meta).
"""

import csv
import logging
import os
import re
import threading
import time
from collections import OrderedDict, defaultdict, deque

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
from flask import Flask, abort, request

load_dotenv()

# ---------- Настройки (берутся из файла .env) ----------
TOKEN = os.environ["WHATSAPP_TOKEN"]                 # постоянный токен из Meta
PHONE_NUMBER_ID = os.environ["PHONE_NUMBER_ID"]      # ID номера бота в Meta
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "moi-sekret-123")
TEACHER_PHONE = os.environ["TEACHER_PHONE"]          # ваш номер, например 996555123456

TEMPLATE_STUDENT = os.environ.get("TEMPLATE_STUDENT", "okuu_tekshiruu")
TEMPLATE_FORWARD = os.environ.get("TEMPLATE_FORWARD", "otvet_uchenika")
STUDENT_LANG = os.environ.get("STUDENT_LANG", "ky_KG")   # язык шаблона для учеников
TEACHER_LANG = os.environ.get("TEACHER_LANG", "ru")      # язык шаблона пересылки вам

SEND_DAYS = os.environ.get("SEND_DAYS", "mon,wed,fri")
SEND_HOUR = int(os.environ.get("SEND_HOUR", "19"))
SEND_MINUTE = int(os.environ.get("SEND_MINUTE", "0"))
TIMEZONE = os.environ.get("TIMEZONE", "Asia/Bishkek")

STUDENTS_FILE = os.environ.get("STUDENTS_FILE", "students.csv")

# ---------- ИИ-помощник (Claude) ----------
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()       # бесплатный ключ из Google AI Studio
AI_ENABLED = bool(GEMINI_API_KEY or ANTHROPIC_API_KEY)
AI_MODEL = os.environ.get("AI_MODEL") or ("gemini-flash-latest" if GEMINI_API_KEY else "claude-haiku-5-5")
AI_DAILY_LIMIT = int(os.environ.get("AI_DAILY_LIMIT", "20"))   # ответов ИИ на ученика в день
COURSE_INFO = os.environ.get(
    "COURSE_INFO",
    "Курс программирования в Okurmen Academy: HTML, CSS, JavaScript, Git, основы веб-разработки.",
)
SYSTEM_PROMPT = f"""Ты — помощник преподавателя в учебном центре Okurmen Academy. Ты общаешься с учениками в WhatsApp.

О курсе: {COURSE_INFO}

Правила:
- Отвечай на том языке, на котором пишет ученик (кыргызский или русский). Если непонятно — по-кыргызски.
- Отвечай коротко и просто, как хороший учитель новичку: обычно 2–6 предложений. Это WhatsApp, длинных статей не пиши.
- Код показывай короткими кусками. Заголовки и таблицы Markdown не используй: WhatsApp их не показывает. Можно *жирный* и ```код```.
- Объясняй и наводи на решение, а не делай домашнее задание целиком за ученика.
- Если ученик просто рассказывает, как дела («жакшы», «всё хорошо»), коротко и тепло ответь и предложи задать вопрос, если он есть.
- Если вопрос не про учёбу и не про программирование — вежливо скажи, что помогаешь только по курсу.
- Если не уверен в ответе, или вопрос про оценки, оплату, расписание, пропуски или личную проблему — не выдумывай: скажи, что передашь вопрос преподавателю и он ответит сам.
- Никогда не выдумывай факты о курсе, датах и ценах."""
API_URL = f"https://graph.facebook.com/v23.0/{PHONE_NUMBER_ID}/messages"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("bot")
app = Flask(__name__)


# ---------- Ученики ----------
def normalize_phone(phone: str) -> str:
    """'+996 (555) 12-34-56' -> '996555123456'"""
    return re.sub(r"\D", "", phone)


def load_students() -> dict:
    """Список учеников -> {телефон: имя}.

    Берётся из переменной STUDENTS (формат: «Айбек:996555111111; Нурай:996700222222»),
    а если её нет — из файла students.csv (колонки: name,phone).
    """
    students = {}
    env_list = os.environ.get("STUDENTS", "").strip()
    if env_list:
        for item in re.split(r"[;\n]", env_list):
            if ":" in item:
                name, phone = item.rsplit(":", 1)
                if name.strip() and normalize_phone(phone):
                    students[normalize_phone(phone)] = name.strip()
        return students
    if not os.path.exists(STUDENTS_FILE):
        return students
    with open(STUDENTS_FILE, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            name = (row.get("name") or "").strip()
            phone = normalize_phone(row.get("phone") or "")
            if name and phone:
                students[phone] = name
    return students


# ---------- Отправка сообщений ----------
def _post(payload: dict) -> dict:
    r = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={"messaging_product": "whatsapp", **payload},
        timeout=30,
    )
    data = r.json()
    if r.status_code != 200:
        raise RuntimeError(data)
    return data


def send_template(to: str, template: str, params: list, lang: str) -> dict:
    return _post({
        "to": to,
        "type": "template",
        "template": {
            "name": template,
            "language": {"code": lang},
            "components": [{
                "type": "body",
                "parameters": [{"type": "text", "text": p} for p in params],
            }],
        },
    })


def send_text(to: str, text: str) -> dict:
    return _post({"to": to, "type": "text", "text": {"body": text}})


def clean_for_template(text: str, limit: int = 900) -> str:
    """В параметрах шаблона нельзя переносы строк и много пробелов подряд."""
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit] or "(пусто)"


# ---------- Рассылка по расписанию ----------
def send_checkin_to_all():
    students = load_students()
    log.info("Рассылка: %d учеников", len(students))
    ok = 0
    for phone, name in students.items():
        try:
            send_template(phone, TEMPLATE_STUDENT, [name], STUDENT_LANG)
            ok += 1
        except Exception as e:  # noqa: BLE001
            log.error("Не удалось отправить %s (%s): %s", name, phone, e)
    log.info("Отправлено: %d из %d", ok, len(students))
    return ok, len(students)


# ---------- Пересылка ответов учителю ----------
def forward_to_teacher(name: str, phone: str, text: str):
    full = f"📩 {name} (+{phone}):\n{text}"
    try:
        # Бесплатно/дешевле, если вы писали боту за последние 24 часа
        send_text(TEACHER_PHONE, full)
    except Exception:  # окно 24 часа закрыто — шлём через шаблон
        send_template(
            TEACHER_PHONE, TEMPLATE_FORWARD,
            [clean_for_template(f"{name} (+{phone})", 100), clean_for_template(text)],
            TEACHER_LANG,
        )


def describe_message(msg: dict) -> str:
    t = msg.get("type")
    if t == "text":
        return msg["text"]["body"]
    if t == "button":
        return msg["button"].get("text", "")
    if t == "interactive":
        inter = msg["interactive"]
        return (inter.get("button_reply") or inter.get("list_reply") or {}).get("title", "")
    return {
        "audio": "🎤 голосовое сообщение",
        "image": "🖼 фото",
        "video": "🎬 видео",
        "document": "📄 файл",
        "sticker": "стикер",
    }.get(t, f"[{t}]")


# ---------- ИИ-ответы ----------
_history = defaultdict(lambda: deque(maxlen=10))   # последние сообщения диалога с каждым учеником
_daily = {}                                        # {телефон: (дата, сколько ответов)}
_seen = OrderedDict()                              # id уже обработанных сообщений (WhatsApp может прислать повтор)
_lock = threading.Lock()


def already_seen(msg_id: str) -> bool:
    with _lock:
        if not msg_id or msg_id in _seen:
            return bool(msg_id)
        _seen[msg_id] = True
        while len(_seen) > 2000:
            _seen.popitem(last=False)
        return False


def ai_allowed(phone: str) -> bool:
    today = time.strftime("%Y-%m-%d")
    with _lock:
        day, count = _daily.get(phone, (today, 0))
        if day != today:
            count = 0
        if count >= AI_DAILY_LIMIT:
            return False
        _daily[phone] = (today, count + 1)
        return True


def _claude(messages: list) -> str:
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={"model": AI_MODEL, "max_tokens": 700, "system": SYSTEM_PROMPT, "messages": messages},
        timeout=60,
    )
    data = r.json()
    if r.status_code != 200:
        raise RuntimeError(data)
    return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text").strip()


def _gemini(messages: list) -> str:
    r = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{AI_MODEL}:generateContent",
        headers={"x-goog-api-key": GEMINI_API_KEY, "content-type": "application/json"},
        json={
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [
                {"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]}
                for m in messages
            ],
            "generationConfig": {"maxOutputTokens": 2048},
        },
        timeout=60,
    )
    data = r.json()
    if r.status_code != 200:
        raise RuntimeError(data)
    parts = ((data.get("candidates") or [{}])[0].get("content") or {}).get("parts", [])
    return "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()


def ask_ai(phone: str, name: str, text: str) -> str:
    hist = _history[phone]
    hist.append({"role": "user", "content": f"{name}: {text}"})
    messages = list(hist)
    while messages and messages[0]["role"] != "user":   # диалог должен начинаться с ученика
        messages.pop(0)
    try:
        answer = _gemini(messages) if GEMINI_API_KEY else _claude(messages)
    except Exception:
        hist.pop()
        raise
    if not answer:
        hist.pop()
        raise RuntimeError("пустой ответ ИИ")
    hist.append({"role": "assistant", "content": answer})
    return answer[:3500]


def handle_student_message(phone: str, name: str, msg: dict):
    text = describe_message(msg)
    log.info("Сообщение от %s: %s", name, text)

    if not AI_ENABLED:
        forward_to_teacher(name, phone, text)
        return

    if msg.get("type") != "text":
        send_text(phone, "Азырынча текст гана окуй алам 🙏 Суроону жазып жибериңизчи.\n"
                         "(Пока я понимаю только текст — напишите вопрос, пожалуйста.)")
        forward_to_teacher(name, phone, text)
        return

    if not ai_allowed(phone):
        forward_to_teacher(name, phone, text + "\n\n(лимит ответов бота на сегодня исчерпан — ответьте сами)")
        return

    try:
        answer = ask_ai(phone, name, text)
        send_text(phone, answer)
        forward_to_teacher(name, phone, f"{text}\n\n🤖 Бот ответил:\n{answer}")
    except Exception as e:  # noqa: BLE001
        log.error("Ошибка ИИ для %s: %s", name, e)
        forward_to_teacher(name, phone, text + "\n\n(бот не смог ответить — ответьте сами)")


def safe(fn, *args):
    try:
        fn(*args)
    except Exception as e:  # noqa: BLE001
        log.error("Ошибка обработки: %s", e)


# ---------- Webhook (сюда WhatsApp присылает ответы) ----------
@app.get("/webhook")
def verify():
    if (request.args.get("hub.mode") == "subscribe"
            and request.args.get("hub.verify_token") == VERIFY_TOKEN):
        return request.args.get("hub.challenge", "")
    abort(403)


@app.post("/webhook")
def incoming():
    data = request.get_json(silent=True) or {}
    students = load_students()
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            for msg in change.get("value", {}).get("messages", []):
                phone = normalize_phone(msg.get("from", ""))
                if phone == normalize_phone(TEACHER_PHONE):
                    # Команды учителя
                    if msg.get("type") == "text" and msg["text"]["body"].strip().lower() == "/рассылка":
                        send_checkin_to_all()
                        send_text(TEACHER_PHONE, "✅ Рассылка отправлена")
                    continue
                if already_seen(msg.get("id", "")):
                    continue
                if phone in students:
                    # Отвечаем в фоне, чтобы WhatsApp сразу получил «ok» и не слал повторы
                    threading.Thread(
                        target=safe, args=(handle_student_message, phone, students[phone], msg), daemon=True
                    ).start()
                else:
                    # Незнакомым номерам ИИ не отвечает — только пересылаем вам
                    threading.Thread(
                        target=safe,
                        args=(forward_to_teacher, "Неизвестный номер", phone, describe_message(msg)),
                        daemon=True,
                    ).start()
    return "ok"


@app.get("/")
def health():
    return f"Бот работает. Учеников: {len(load_students())}"


@app.get("/send")
def send_now():
    """Запустить рассылку из браузера: /send?key=<VERIFY_TOKEN>"""
    if request.args.get("key") != VERIFY_TOKEN:
        abort(403)
    ok, total = send_checkin_to_all()
    return f"Рассылка отправлена: {ok} из {total}"


PRIVACY_HTML = """<!doctype html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Политика конфиденциальности — Okurmen Academy</title>
<style>body{font-family:system-ui,sans-serif;max-width:720px;margin:40px auto;padding:0 16px;line-height:1.6;color:#222}</style>
</head><body>
<h1>Политика конфиденциальности</h1>
<p>Okurmen Academy использует WhatsApp-бота, чтобы связываться со своими учениками
и узнавать, как проходит их учёба.</p>
<h2>Какие данные мы обрабатываем</h2>
<ul>
<li>Имя ученика и номер телефона WhatsApp, которые ученик сообщил учебному центру.</li>
<li>Сообщения, которые ученик отправляет боту в ответ.</li>
</ul>
<h2>Зачем</h2>
<p>Только для связи с учениками по вопросам обучения. Ответы учеников передаются их преподавателю.
Мы не продаём и не передаём данные третьим лицам, кроме Meta (WhatsApp), через которую доставляются сообщения.</p>
<h2>Хранение</h2>
<p>Бот не хранит переписку в базе данных: сообщения пересылаются преподавателю и остаются в WhatsApp.</p>
<h2>Как отказаться и удалить данные</h2>
<p>Чтобы больше не получать сообщения или удалить свои данные, напишите об этом боту или преподавателю —
номер будет удалён из списка рассылки.</p>
<p>Контакт: """ + os.environ.get("CONTACT_EMAIL", "bsainaev@gmail.com") + """</p>
</body></html>"""


@app.get("/privacy")
def privacy():
    return PRIVACY_HTML


# ---------- Запуск ----------
scheduler = BackgroundScheduler(timezone=TIMEZONE)
if SEND_DAYS.strip().lower() in ("", "none", "off"):
    log.info("Встроенное расписание выключено (рассылку запускает /send)")
else:
    scheduler.add_job(
        send_checkin_to_all,
        CronTrigger(day_of_week=SEND_DAYS, hour=SEND_HOUR, minute=SEND_MINUTE, timezone=TIMEZONE),
    )
    log.info("Расписание: %s в %02d:%02d (%s)", SEND_DAYS, SEND_HOUR, SEND_MINUTE, TIMEZONE)
scheduler.start()
log.info("ИИ-ответы: %s", "включены (" + AI_MODEL + ")" if AI_ENABLED else "выключены")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))