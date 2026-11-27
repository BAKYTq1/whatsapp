"""
Ответы бота без ИИ — на правилах (if / else по ключевым словам).

Как добавить свой ответ:
  скопируйте любой блок в RULES и поменяйте слова и текст.
  "words"  — слова, по которым бот узнаёт тему (маленькими буквами, можно часть слова);
  "answer" — что бот ответит.
Бот выбирает правило, в котором совпало больше всего слов.
"""

import re

RULES = [
    # ---------- Приветствие и «как дела» ----------
    {
        "words": ["салам", "саламатсызбы", "привет", "здравств", "ассалам", "кандайсыз", "кандайсың"],
        "answer": "Салам! 👋 Мен Okurmen Academy'нин жардамчы ботумун. Сабак боюнча суроо болсо жазыңыз — "
                  "HTML, CSS, JavaScript, Git боюнча жардам берем.",
    },
    {
        "words": ["жакшы", "жаман эмес", "нормально", "хорошо", "норм", "баары жакшы", "все хорошо", "всё хорошо"],
        "answer": "Азаматсыз! 💪 Ушундай эле улантыңыз. Кандайдыр бир тема түшүнүксүз болсо, жазып коюңуз.",
    },
    {
        "words": ["кыйын", "түшүнбөй", "түшүнгөн жокмун", "сложно", "трудно", "не понимаю", "не понял", "не поняла"],
        "answer": "Кыйын болсо — бул нормалдуу, баары ушундан өтөт 🙂 Кайсы тема же кайсы тапшырма кыйын болуп "
                  "жатканын жазыңыз, мугалимге да жеткирем.",
    },
    {
        "words": ["рахмат", "спасибо", "чоң рахмат", "ыракмат"],
        "answer": "Эч нерсе эмес! 😊 Дагы суроо болсо жазыңыз.",
    },

    # ---------- HTML ----------
    {
        "words": ["html", "тег", "teg", "тэг"],
        "answer": "*HTML* — бул беттин скелети. Ар бир элемент тег менен жазылат:\n"
                  "```<h1>Аталыш</h1>\n<p>Текст</p>\n<a href=\"https://google.com\">Шилтеме</a>```\n"
                  "Көпчүлүк тегдер ачылат жана жабылат: <p> ... </p>.",
    },
    {
        "words": ["картинка", "сүрөт", "img", "изображен"],
        "answer": "Сүрөт кошуу үчүн *img* тегин колдонуңуз:\n"
                  "```<img src=\"photo.jpg\" alt=\"Сүрөттүн сүрөттөмөсү\">```\n"
                  "src — файлдын жолу, alt — сүрөт жүктөлбөсө көрүнгөн текст.",
    },
    {
        "words": ["форма", "form", "input", "кнопка", "button", "баскыч"],
        "answer": "Форма мисалы:\n"
                  "```<form>\n  <input type=\"text\" placeholder=\"Атыңыз\">\n  <button>Жөнөтүү</button>\n</form>```",
    },

    # ---------- CSS ----------
    {
        "words": ["css", "стиль", "style", "түс", "цвет", "color"],
        "answer": "*CSS* — бул беттин көрүнүшү. Мисалы:\n"
                  "```h1 {\n  color: blue;\n  font-size: 32px;\n}```\n"
                  "Адегенде селектор (h1, .class, #id), анан фигуралык кашаада касиеттер.",
    },
    {
        "words": ["flex", "флекс", "flexbox"],
        "answer": "*Flexbox* элементтерди катарга же мамыга тизет:\n"
                  "```.box {\n  display: flex;\n  justify-content: center; /* горизонталь */\n"
                  "  align-items: center;     /* вертикаль */\n  gap: 10px;\n}```",
    },
    {
        "words": ["grid", "грид"],
        "answer": "*Grid* — таблица сыяктуу тор:\n"
                  "```.box {\n  display: grid;\n  grid-template-columns: 1fr 1fr 1fr; /* 3 мамыча */\n  gap: 16px;\n}```",
    },
    {
        "words": ["центр", "ортого", "по центру", "center"],
        "answer": "Элементти ортого коюунун эң оңой жолу:\n"
                  "```.parent {\n  display: flex;\n  justify-content: center;\n  align-items: center;\n}```",
    },
    {
        "words": ["margin", "padding", "отступ", "аралык"],
        "answer": "*padding* — элементтин ичиндеги аралык, *margin* — сыртындагы аралык.\n"
                  "```.card {\n  padding: 16px;\n  margin: 20px;\n}```",
    },
    {
        "words": ["адаптив", "media", "медиа", "телефон", "мобил"],
        "answer": "Телефонго ылайыктоо үчүн media query:\n"
                  "```@media (max-width: 768px) {\n  .menu { display: none; }\n}```",
    },

    # ---------- JavaScript ----------
    {
        "words": ["let", "const", "var", "переменн", "өзгөрмө"],
        "answer": "*let* — маанисин кийин өзгөртсө болот, *const* — өзгөрбөйт, *var* — эски жол, колдонбогонуңуз оң.\n"
                  "```let age = 18;\nage = 19;      // болот\nconst name = \"Айбек\";\nname = \"Нурай\"; // ката!```",
    },
    {
        "words": ["function", "функци"],
        "answer": "Функция — кайра-кайра колдонулуучу код:\n"
                  "```function salam(name) {\n  return \"Салам, \" + name;\n}\nsalam(\"Айбек\");```\n"
                  "Же жебе функция: `const salam = (name) => \"Салам, \" + name;`",
    },
    {
        "words": ["if", "else", "шарт", "условие"],
        "answer": "Шарт мисалы:\n"
                  "```if (age >= 18) {\n  console.log(\"Чоң киши\");\n} else {\n  console.log(\"Жаш\");\n}```",
    },
    {
        "words": ["цикл", "for", "while", "loop", "кайталоо"],
        "answer": "Цикл мисалы — 1ден 5ке чейин чыгаруу:\n"
                  "```for (let i = 1; i <= 5; i++) {\n  console.log(i);\n}```",
    },
    {
        "words": ["массив", "array", "map", "filter", "тизме"],
        "answer": "Массив — маанилердин тизмеси:\n"
                  "```const nums = [1, 2, 3];\nnums.push(4);                 // кошуу\n"
                  "nums.map(n => n * 2);         // [2, 4, 6, 8]\nnums.filter(n => n > 2);      // [3, 4]```",
    },
    {
        "words": ["объект", "object", "обьект"],
        "answer": "Объект — ачкыч: маани түгөйлөрү:\n"
                  "```const user = { name: \"Айбек\", age: 18 };\nconsole.log(user.name); // Айбек```",
    },
    {
        "words": ["dom", "queryselector", "getelementbyid", "addeventlistener", "click", "клик"],
        "answer": "Баскычты басканда бир нерсе кылуу:\n"
                  "```const btn = document.querySelector(\"#btn\");\nbtn.addEventListener(\"click\", () => {\n"
                  "  alert(\"Басылды!\");\n});```",
    },
    {
        "words": ["fetch", "api", "async", "await", "промис", "promise"],
        "answer": "Серверден маалымат алуу:\n"
                  "```async function load() {\n  const res = await fetch(\"https://api.example.com/data\");\n"
                  "  const data = await res.json();\n  console.log(data);\n}```",
    },
    {
        "words": ["ошибка", "ката", "error", "иштебей", "не работает", "undefined", "null"],
        "answer": "Ката чыкса:\n1) Браузерде F12 → *Console* ачып, кызыл катаны окуңуз.\n"
                  "2) Кайсы сапта экенин караңыз.\n3) Ката текстин мага же мугалимге жөнөтүңүз — "
                  "кодуңуз менен кошо жазсаңыз, тезирээк жардам беребиз.",
    },

    # ---------- Git ----------
    {
        "words": ["git", "гит", "github", "гитхаб", "commit", "push", "коммит", "пуш"],
        "answer": "Git негизги буйруктары:\n"
                  "```git add .\ngit commit -m \"эмне өзгөрдү\"\ngit push```\n"
                  "Биринчи жолу: git init → git remote add origin <шилтеме> → git push -u origin main",
    },

    # ---------- Организационные вопросы → преподавателю ----------
    {
        "words": ["төлөм", "оплата", "акча", "деньги", "баа", "цена", "расписание", "жадыбал", "сабак качан",
                  "когда урок", "пропуск", "келе албайм", "не приду", "оценка", "сертификат"],
        "answer": "Бул суроону мугалимге жөнөттүм — ал өзү жооп берет 🙏",
        "teacher": True,
    },
]

DEFAULT_ANSWER = ("Суроонузду түшүндүм 🙏 Мугалимге жөнөттүм, ал жакында жооп берет.\n"
                  "Тезирээк жардам алуу үчүн темасын жазыңыз: мисалы, «flex», «let const», «git push».")


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().replace("ё", "е")).strip()


def find_answer(text: str):
    """Возвращает (ответ, нужно_ли_позвать_учителя)."""
    t = _norm(text)
    best, best_score = None, 0
    for rule in RULES:
        score = 0
        for w in rule["words"]:
            w = _norm(w)
            # короткие латинские слова (if, for, let) — только целым словом, чтобы не ловить «before», «letter»
            if len(w) <= 4 and re.fullmatch(r"[a-z]+", w):
                if re.search(rf"\b{re.escape(w)}\b", t):
                    score += 1
            elif w in t:
                score += 1
        if score > best_score:
            best, best_score = rule, score
    if best is None:
        return DEFAULT_ANSWER, True
    return best["answer"], bool(best.get("teacher"))