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
        "words": ["салам", "саламатсызбы", "привет", "здравств", "ассалам", "ассалом", "алейкум", "алейкуm",
                  "кандайсыз", "кандайсың", "добрый"],
        "low": True,   # приветствие — только если в сообщении нет настоящего вопроса
        "answer": "Салам! 👋 Мен Okurmen Academy'нин жардамчы ботумун. Сабак боюнча суроо болсо жазыңыз — "
                  "HTML, CSS, JavaScript, Git боюнча жардам берем.",
    },
    {
        "words": ["жакшы", "жаман эмес", "нормально", "хорошо", "норм", "баары жакшы", "все хорошо", "всё хорошо",
                  "жшк", "жакшы рахмат"],
        "low": True,
        "answer": "Азаматсыз! 💪 Ушундай эле улантыңыз. Кандайдыр бир тема түшүнүксүз болсо, жазып коюңуз.",
    },
    {
        "words": ["кыйын", "түшүнбөй", "түшүнгөн жокмун", "сложно", "трудно", "не понимаю", "не понял", "не поняла"],
        "answer": "Кыйын болсо — бул нормалдуу, баары ушундан өтөт 🙂 Кайсы тема же кайсы тапшырма кыйын болуп "
                  "жатканын жазыңыз, мугалимге да жеткирем.",
    },
    {
        "words": ["рахмат", "спасибо", "чоң рахмат", "ыракмат"],
        "low": True,
        "answer": "Эч нерсе эмес! 😊 Дагы суроо болсо жазыңыз.",
    },

    # ---------- HTML ----------
    {
        "words": ["html", "тег", "teg", "тэг"],
        "general": True,   # общая тема: если есть более точная — отвечаем по ней
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
        "general": True,   # общая тема: если есть более точная — отвечаем по ней
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
        "general": True,   # общая тема: если есть более точная — отвечаем по ней
        "answer": "Ката чыкса:\n1) Браузерде F12 → *Console* ачып, кызыл катаны окуңуз.\n"
                  "2) Кайсы сапта экенин караңыз.\n3) Ката текстин мага же мугалимге жөнөтүңүз — "
                  "кодуңуз менен кошо жазсаңыз, тезирээк жардам беребиз.",
    },

    # ---------- Git ----------
    {
        "words": ["git", "гит", "github", "гитхаб", "commit", "push", "коммит", "пуш"],
        "general": True,   # общая тема: если есть более точная — отвечаем по ней
        "answer": "Git негизги буйруктары:\n"
                  "```git add .\ngit commit -m \"эмне өзгөрдү\"\ngit push```\n"
                  "Биринчи жолу: git init → git remote add origin <шилтеме> → git push -u origin main",
    },

    # ---------- Ещё HTML ----------
    {
        "words": ["структура", "шаблон", "doctype", "head", "body", "! tab", "заготовка"],
        "answer": "HTML барагынын негизги түзүлүшү:\n"
                  "```<!DOCTYPE html>\n<html lang=\"ky\">\n<head>\n  <meta charset=\"UTF-8\">\n"
                  "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
                  "  <title>Барак</title>\n</head>\n<body>\n\n</body>\n</html>```\n"
                  "VS Code'до *!* жазып, Tab бассаңыз — ушул өзү чыгат.",
    },
    {
        "words": ["список", "тизмек", "ul", "ol", "li"],
        "answer": "Тизме:\n```<ul>          <!-- чекиттер менен -->\n  <li>Бир</li>\n  <li>Эки</li>\n</ul>\n\n"
                  "<ol>          <!-- номерлер менен -->\n  <li>Биринчи</li>\n</ol>```",
    },
    {
        "words": ["таблица", "table", "таблиц", "жадыбал түзүү"],
        "answer": "Таблица:\n```<table>\n  <tr><th>Аты</th><th>Жашы</th></tr>\n"
                  "  <tr><td>Айбек</td><td>18</td></tr>\n</table>```\n"
                  "tr — сап, th — аталыш уячасы, td — кадимки уяча.",
    },
    {
        "words": ["ссылк", "шилтеме", "href", "переход", "target"],
        "answer": "Шилтеме:\n```<a href=\"https://google.com\" target=\"_blank\">Google</a>```\n"
                  "target=\"_blank\" — жаңы өтмөктө ачат. Беттин ичиндеги бөлүккө: href=\"#about\" жана "
                  "ал жерге id=\"about\" коюңуз.",
    },
    {
        "words": ["div", "span", "блочн", "строчн", "inline"],
        "answer": "*div* — блоктук элемент: өзүнчө сапты ээлейт. *span* — саптык: тексттин ичинде калат.\n"
                  "```<div>Өзүнчө блок</div>\n<p>Бул <span style=\"color:red\">кызыл</span> сөз</p>```",
    },
    {
        "words": ["семантик", "header", "footer", "nav", "section", "main", "article"],
        "answer": "Семантикалык тегдер — маанисин айтып турган div'дер:\n"
                  "```<header>Шапка</header>\n<nav>Меню</nav>\n<main>\n  <section>Бөлүм</section>\n</main>\n"
                  "<footer>Ылдыйкы бөлүк</footer>```\nКодду окууга жеңил жана Google үчүн да жакшы.",
    },
    {
        "words": ["видео", "video", "iframe", "youtube", "ютуб"],
        "answer": "YouTube видеосун кошуу: видеонун астындагы *Бөлүшүү → Встроить* баскычынан iframe кодун "
                  "көчүрүп, HTML'ге коюңуз. Өз файлыңыз болсо:\n```<video src=\"video.mp4\" controls></video>```",
    },
    {
        "words": ["коммент", "комментарий", "түшүндүрмө"],
        "answer": "Комментарийлер:\n```<!-- HTML -->\n/* CSS */\n// JavaScript (бир сап)\n/* JavaScript (көп сап) */```\n"
                  "VS Code'до тез жазуу: *Ctrl + /*",
    },

    # ---------- Ещё CSS ----------
    {
        "words": ["подключ", "туташтыр", "link", "файл css", "style.css", "кошуу css"],
        "answer": "CSS файлын HTML'ге туташтыруу — <head> ичине:\n"
                  "```<link rel=\"stylesheet\" href=\"style.css\">```\n"
                  "JS файлын — </body> алдына же head'ке defer менен:\n```<script src=\"script.js\" defer></script>```",
    },
    {
        "words": ["класс", "class", "селектор", "selector", "#id", ".class"],
        "answer": "Селекторлор:\n```p { }          /* бардык <p> */\n.card { }      /* class=\"card\" */\n"
                  "#main { }      /* id=\"main\" */\n.card p { }    /* .card ичиндеги p */```\n"
                  "class бир нече элементке, id — бирөөнө гана.",
    },
    {
        "words": ["position", "позиц", "absolute", "relative", "fixed", "sticky"],
        "answer": "*position*:\n• relative — өз ордунан жылдырат\n• absolute — эң жакын relative ата-энесине карата\n"
                  "• fixed — экранга бекитилет (скролдо кыймылдабайт)\n• sticky — скролдо жабышып калат\n"
                  "```.parent { position: relative; }\n.badge { position: absolute; top: 0; right: 0; }```",
    },
    {
        "words": ["z-index", "үстүнө", "поверх", "перекрыва"],
        "answer": "Бир элементти экинчисинин үстүнө чыгаруу үчүн *z-index* колдонуңуз (position керек):\n"
                  "```.modal {\n  position: fixed;\n  z-index: 100;\n}```\nСаны чоң болгон үстүндө турат.",
    },
    {
        "words": ["шрифт", "font", "арип", "google fonts"],
        "answer": "Шрифт:\n```body {\n  font-family: 'Roboto', sans-serif;\n  font-size: 16px;\n  font-weight: 400;\n}```\n"
                  "Google Fonts'тон: fonts.google.com → шрифтти тандап → <link> кодун head'ке коюңуз.",
    },
    {
        "words": ["border-radius", "закругл", "тегерек", "радиус", "border"],
        "answer": "Чек жана бурчтарды тегеректөө:\n```.card {\n  border: 1px solid #ccc;\n  border-radius: 12px;\n}\n"
                  ".avatar { border-radius: 50%; } /* толук тегерек */```",
    },
    {
        "words": ["тень", "shadow", "көлөкө"],
        "answer": "Көлөкө:\n```.card {\n  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);\n}```\n"
                  "Тексттин көлөкөсү: `text-shadow: 1px 1px 2px gray;`",
    },
    {
        "words": ["hover", "ховер", "наведен", "transition", "анимац", "animation", "keyframes"],
        "answer": "Чычкан менен үстүнө келгенде өзгөрүү:\n```.btn {\n  background: blue;\n  transition: 0.3s;\n}\n"
                  ".btn:hover {\n  background: darkblue;\n  transform: scale(1.05);\n}```\n"
                  "Татаалыраак анимация үчүн @keyframes колдонулат.",
    },
    {
        "words": ["background", "арка план", "задний фон", "фоновое", "фон сайта", "фон картин"],
        "answer": "Фон:\n```.hero {\n  background-color: #f5f5f5;\n  background-image: url(\"bg.jpg\");\n"
                  "  background-size: cover;\n  background-position: center;\n}```",
    },
    {
        "words": ["rem", "em", "vh", "vw", "px", "единиц", "бирдик", "процент"],
        "answer": "Өлчөө бирдиктери:\n• px — так пиксель\n• % — ата-энесинен пайыз\n"
                  "• rem — html'дин шрифтине карата (1rem = 16px)\n• vh / vw — экрандын бийиктиги / туурасынан пайыз\n"
                  "Мисал: `height: 100vh;` — толук экран.",
    },
    {
        "words": ["box-sizing", "размер блока", "ширина", "width", "height", "туурасы", "бийиктиги"],
        "answer": "Өлчөмдөр туура эсептелиши үчүн дайыма ушуну файлдын башына жазыңыз:\n"
                  "```* {\n  margin: 0;\n  padding: 0;\n  box-sizing: border-box;\n}```\n"
                  "Анан `width: 300px;` padding менен кошо 300px болот.",
    },
    {
        "words": ["display", "none", "скрыть", "жашыр", "block", "inline-block"],
        "answer": "*display*:\n• none — элементти жашырат\n• block — өзүнчө сап\n• inline — тексттин ичинде\n"
                  "• inline-block — тексттин ичинде, бирок width/height иштейт\n• flex / grid — тизүү үчүн",
    },
    {
        "words": ["бургер", "burger", "меню", "menu", "навбар", "navbar"],
        "answer": "Меню жасоонун жөнөкөй жолу:\n```<nav class=\"menu\">\n  <a href=\"#\">Башкы</a>\n  <a href=\"#about\">Биз жөнүндө</a>\n</nav>```\n"
                  "```.menu { display: flex; gap: 20px; }```\n"
                  "Телефондо бургер-меню үчүн JS менен класс которуштурулат: `menu.classList.toggle(\"open\")`.",
    },

    # ---------- Ещё JavaScript ----------
    {
        "words": ["console.log", "консол", "console", "вывести", "чыгаруу"],
        "answer": "Маанини текшерүү үчүн:\n```console.log(\"Салам\", name);```\nНатыйжаны браузерде *F12 → Console* "
                  "өтмөгүнөн көрөсүз. Ката издегенде эң жакшы жардамчы ушул.",
    },
    {
        "words": ["строк", "string", "шаблонн", "template", "кавычк", "бэктик", "backtick"],
        "answer": "Сап менен иштөө:\n```const name = \"Айбек\";\nconst text = `Салам, ${name}!`;  // backtick ` ` менен\n"
                  "text.length;         // узундугу\ntext.toUpperCase();  // ЧОҢ ТАМГА\ntext.includes(\"Салам\"); // true```",
    },
    {
        "words": ["===", "==", "сравнен", "салыштыр", "равно", "барабар"],
        "answer": "*==* типти эске албайт, *===* типти да текшерет. Дайыма === колдонуңуз:\n"
                  "```5 == \"5\"   // true  (жаман)\n5 === \"5\"  // false (туура)```",
    },
    {
        "words": ["typeof", "тип данных", "маалымат тиби", "number", "boolean", "типы"],
        "answer": "Маалымат типтери: string, number, boolean, null, undefined, object, array.\n"
                  "```typeof \"салам\"  // \"string\"\ntypeof 5        // \"number\"\ntypeof true     // \"boolean\"\n"
                  "Array.isArray([1,2]) // true```",
    },
    {
        "words": ["switch", "case"],
        "answer": "switch — көп шарт үчүн:\n```switch (day) {\n  case 1:\n    console.log(\"Дүйшөмбү\");\n    break;\n"
                  "  case 2:\n    console.log(\"Шейшемби\");\n    break;\n  default:\n    console.log(\"Башка күн\");\n}```",
    },
    {
        "words": ["innerhtml", "textcontent", "innertext", "изменить текст", "текстти өзгөрт"],
        "answer": "Элементтин текстин өзгөртүү:\n```const title = document.querySelector(\"h1\");\ntitle.textContent = \"Жаңы аталыш\";\n"
                  "title.innerHTML = \"<b>Калың</b> текст\";```\nТекст гана болсо textContent коопсузураак.",
    },
    {
        "words": ["classlist", "toggle", "add class", "класс кош", "добавить класс"],
        "answer": "Класс кошуу / алып салуу:\n```el.classList.add(\"active\");\nel.classList.remove(\"active\");\n"
                  "el.classList.toggle(\"active\"); // бар болсо алат, жок болсо кошот```",
    },
    {
        "words": ["value", "инпут", "получить значение", "маанисин ал", "preventdefault", "submit"],
        "answer": "Формадан маани алуу:\n```const form = document.querySelector(\"form\");\nform.addEventListener(\"submit\", (e) => {\n"
                  "  e.preventDefault();          // барак жаңырбашы үчүн\n"
                  "  const name = document.querySelector(\"#name\").value;\n  console.log(name);\n});```",
    },
    {
        "words": ["localstorage", "сохранить", "сактоо", "storage"],
        "answer": "Браузерде маалымат сактоо:\n```localStorage.setItem(\"name\", \"Айбек\");\nlocalStorage.getItem(\"name\");   // \"Айбек\"\n"
                  "// массив же объект үчүн JSON керек:\nlocalStorage.setItem(\"todos\", JSON.stringify(todos));\n"
                  "const todos = JSON.parse(localStorage.getItem(\"todos\")) || [];```",
    },
    {
        "words": ["json", "stringify", "parse"],
        "answer": "*JSON* — маалыматты текст түрүндө сактоо/жөнөтүү:\n```JSON.stringify({ a: 1 })  // '{\"a\":1}'\n"
                  "JSON.parse('{\"a\":1}')     // { a: 1 }```",
    },
    {
        "words": ["settimeout", "setinterval", "таймер", "timer", "задержк", "кечиктир"],
        "answer": "Таймерлер:\n```setTimeout(() => console.log(\"2 секунддан кийин\"), 2000);\n\n"
                  "const id = setInterval(() => console.log(\"ар секунд\"), 1000);\nclearInterval(id); // токтотуу```",
    },
    {
        "words": ["random", "рандом", "случайн", "кокустан", "math"],
        "answer": "Кокус сан 1ден 10го чейин:\n```const n = Math.floor(Math.random() * 10) + 1;```\n"
                  "Башка пайдалуулар: Math.round(), Math.max(1, 5), Math.min().",
    },
    {
        "words": ["foreach", "find", "reduce", "some", "every", "sort", "сортиров"],
        "answer": "Массив методдору:\n```nums.forEach(n => console.log(n));       // ар бирин айлануу\n"
                  "nums.find(n => n > 2);                   // биринчи табылганы\nnums.reduce((sum, n) => sum + n, 0);     // суммасы\n"
                  "nums.sort((a, b) => a - b);              // өсүү тартибинде```",
    },
    {
        "words": ["try", "catch", "обработка ошибок"],
        "answer": "Катаны кармоо:\n```try {\n  const data = JSON.parse(text);\n} catch (err) {\n  console.log(\"Ката:\", err.message);\n}```",
    },
    {
        "words": ["script", "скрипт", "не подключ", "туташпай", "defer"],
        "answer": "Скрипт иштебесе, текшериңиз:\n1) `<script src=\"script.js\" defer></script>` — жолу туурабы?\n"
                  "2) defer бар болсо, HTML жүктөлгөндөн кийин иштейт.\n3) F12 → Console'до кызыл ката барбы?",
    },
    {
        "words": ["класс js", "class constructor", "constructor", "ооп", "oop", "this"],
        "answer": "JS'те класс:\n```class User {\n  constructor(name) {\n    this.name = name;\n  }\n  hello() {\n"
                  "    return `Салам, ${this.name}`;\n  }\n}\nconst u = new User(\"Айбек\");\nu.hello();```",
    },

    # ---------- React ----------
    {
        "words": ["react", "реакт", "компонент", "component", "jsx"],
        "answer": "React'те компонент — бул функция, ал JSX кайтарат:\n```function Card({ title }) {\n  return <div className=\"card\">{title}</div>;\n}\n\n"
                  "<Card title=\"Салам\" />```\nДолбоор түзүү: `npm create vite@latest` → React тандаңыз.",
    },
    {
        "words": ["usestate", "стейт", "state", "состояни"],
        "answer": "useState — компоненттин эс тутуму:\n```import { useState } from \"react\";\n\nfunction Counter() {\n"
                  "  const [count, setCount] = useState(0);\n  return <button onClick={() => setCount(count + 1)}>{count}</button>;\n}```",
    },
    {
        "words": ["useeffect", "эффект", "effect"],
        "answer": "useEffect — компонент чыкканда же маани өзгөргөндө код иштетүү:\n```useEffect(() => {\n"
                  "  fetch(\"/api/users\").then(r => r.json()).then(setUsers);\n}, []); // [] — бир гана жолу```",
    },
    {
        "words": ["props", "пропс"],
        "answer": "props — компонентке сырттан берилүүчү маалымат:\n```function Hello({ name }) {\n  return <h1>Салам, {name}</h1>;\n}\n\n"
                  "<Hello name=\"Нурай\" />```",
    },
    {
        "words": ["key", "ключ", "react", "список react"],
        "answer": "React'те тизме чыгарганда ар бир элементке уникалдуу *key* керек:\n"
                  "```{users.map(u => <li key={u.id}>{u.name}</li>)}```",
    },

    # ---------- Ещё Git ----------
    {
        "words": ["clone", "клон", "скачать репо", "жүктөп ал"],
        "answer": "Репозиторийди компьютерге алуу:\n```git clone https://github.com/user/project.git\ncd project```",
    },
    {
        "words": ["branch", "ветк", "бутак", "checkout", "switch -c"],
        "answer": "Бутактар:\n```git branch                # тизме\ngit checkout -b feature    # жаңы бутак түзүп өтүү\n"
                  "git checkout main          # main'ге кайтуу\ngit merge feature          # бириктирүү```",
    },
    {
        "words": ["pull", "пулл", "обновить", "жаңырт"],
        "answer": "GitHub'тагы акыркы өзгөрүүлөрдү алуу:\n```git pull```\nPush'тан мурун pull кылуу — жакшы адат.",
    },
    {
        "words": ["конфликт", "conflict", "merge conflict"],
        "answer": "Конфликт чыкса: файлды ачыңыз, <<<<<<< жана >>>>>>> белгилеринин ортосунан керектүү кодду калтырып, "
                  "белгилерди өчүрүңүз. Анан:\n```git add .\ngit commit -m \"fix conflict\"```\n"
                  "VS Code'до «Accept Current / Incoming» баскычтары жардам берет.",
    },
    {
        "words": ["gitignore", "игнор", "node_modules"],
        "answer": "GitHub'ка жүктөлбөшү керек болгон файлдар үчүн долбоордун түбүнө *.gitignore* файлын түзүңүз:\n"
                  "```node_modules/\n.env\n.DS_Store```",
    },
    {
        "words": ["status", "статус", "log", "история коммит"],
        "answer": "Абалды текшерүү:\n```git status     # эмне өзгөрдү\ngit log --oneline   # коммиттердин тарыхы```",
    },
    {
        "words": ["pages", "хостинг", "деплой", "deploy", "сайтты жүктө", "опубликовать сайт", "vercel", "netlify"],
        "answer": "Сайтты акысыз интернетке чыгаруу:\n• *GitHub Pages*: репо → Settings → Pages → Branch: main → Save\n"
                  "• *Vercel* же *Netlify*: GitHub менен кирип, репону тандасаңыз болду.",
    },
    {
        "words": ["rejected", "failed to push", "permission denied", "403"],
        "answer": "Push өтпөсө:\n1) Алгач `git pull` кылыңыз, анан кайра `git push`.\n"
                  "2) «Permission denied / 403» болсо — бул репого укугуңуз жок же башка аккаунт менен кирдиңиз.\n"
                  "Ката текстин мугалимге жөнөтүңүз.",
    },

    # ---------- Инструменты ----------
    {
        "words": ["vs code", "vscode", "вскод", "редактор", "extension", "расширен", "кеңейтүү"],
        "answer": "VS Code үчүн пайдалуу кеңейтүүлөр: *Live Server*, *Prettier*, *Auto Rename Tag*, *ES7 React snippets*.\n"
                  "Пайдалуу баскычтар: Ctrl+/ — комментарий, Alt+Shift+F — кодду тегиздөө, Ctrl+D — окшош сөздү тандоо.",
    },
    {
        "words": ["live server", "лайв сервер", "открыть сайт", "браузерде ач"],
        "answer": "VS Code'до *Live Server* кеңейтүүсүн орнотуп, index.html'ге оң баскыч → *Open with Live Server*. "
                  "Сактаган сайын барак өзү жаңырат.",
    },
    {
        "words": ["npm", "node", "nodejs", "install", "установ", "орнот"],
        "answer": "Node.js'ти nodejs.org'дон орнотуңуз (LTS версиясы). Анан терминалда:\n"
                  "```node -v          # текшерүү\nnpm install       # долбоордун пакеттерин орнотуу\nnpm run dev       # иштетүү```",
    },

    # ---------- Учёба ----------
    {
        "words": ["үй тапшырма", "домашк", "домашнее", "дз", "тапшырма"],
        "answer": "Үй тапшырма боюнча: адегенде тапшырманы бөлүктөргө бөлүңүз жана ар бирин өзүнчө жасаңыз. "
                  "Кайсы бөлүгүндө токтоп калдыңыз — так жазыңыз (кодуңуз менен), жардам берем 🙂",
    },
    {
        "words": ["как учить", "кантип үйрөн", "с чего начать", "эмнеден баштайм", "совет", "кеңеш", "мотивац"],
        "answer": "Кеңеш: күн сайын аз-аздан (30–60 мүнөт) код жазыңыз — бул жумасына бир жолу көп жазгандан пайдалуураак. "
                  "Окуган нерсеңизди дароо кичине долбоордо колдонуп көрүңүз. Ката — бул окуунун бөлүгү 💪",
    },
    {
        "words": ["практика", "сайт для", "задачи", "маселе", "тренир", "где практиковать"],
        "answer": "Практика үчүн: *freecodecamp.org* (HTML/CSS/JS), *codewars.com* (JS маселелер), "
                  "*flexboxfroggy.com* жана *cssgridgarden.com* (оюн аркылуу CSS).",
    },

    # ---------- Организационные вопросы → преподавателю ----------
    {
        "words": ["төлөм", "оплата", "акча", "деньги", "баа", "цена", "расписание", "жадыбал", "сабак качан",
                  "когда урок", "пропуск", "келе албайм", "не приду", "оценка", "сертификат", "кайда жөнөтөм",
                  "куда сдавать", "дедлайн", "deadline", "мөөнөт", "ооруп", "болею", "договор", "келишим"],
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
        # настоящая тема всегда важнее приветствия: «Салам, flex кантип?» → ответ про flex
        if score and not rule.get("low"):
            score += 50 if rule.get("general") else 100
            if rule.get("teacher"):
                score += 20   # оплата, сроки, пропуски — всегда к преподавателю
        if score > best_score:
            best, best_score = rule, score
    if best is None:
        return DEFAULT_ANSWER, True
    return best["answer"], bool(best.get("teacher"))