"""
WhatsApp-бот для учеников.

Что делает:
  1. По расписанию (по умолчанию Пн/Ср/Пт в 19:00) пишет каждому ученику
     из students.csv: «Привет, <имя>! Как идёт учёба? ...»
  2. Когда ученик отвечает — пересылает ответ учителю в WhatsApp.

Работает через официальный WhatsApp Cloud API (Meta).
"""

import csv
import logging
import os
import re

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
                name = students.get(phone, "Неизвестный номер")
                text = describe_message(msg)
                log.info("Ответ от %s: %s", name, text)
                try:
                    forward_to_teacher(name, phone, text)
                except Exception as e:  # noqa: BLE001
                    log.error("Не удалось переслать учителю: %s", e)
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
scheduler.add_job(
    send_checkin_to_all,
    CronTrigger(day_of_week=SEND_DAYS, hour=SEND_HOUR, minute=SEND_MINUTE, timezone=TIMEZONE),
)
scheduler.start()
log.info("Расписание: %s в %02d:%02d (%s)", SEND_DAYS, SEND_HOUR, SEND_MINUTE, TIMEZONE)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
