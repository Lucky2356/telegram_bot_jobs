from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton, InlineKeyboardMarkup
from enum import StrEnum


class WizardAction(StrEnum):
    NOOP = "noop"
    KW_GROUP_SELECT = "kwg"
    KW_GROUP_BACK = "kwg_bk"
    KEYWORD_TOGGLE = "kw"
    KEYWORD_DONE = "kw_done"
    EXCLUDE_TOGGLE = "ex_kw"
    EXCLUDE_DONE = "ex_done"
    CITY_SELECT = "city"
    CITY_DONE_SKIP = "city_done"
    EXPERIENCE_SELECT = "exp"
    SALARY_SELECT = "sal"
    EMPLOYMENT_TOGGLE = "emp"
    EMPLOYMENT_DONE = "emp_done"
    SITE_TOGGLE = "site"
    SITE_DONE = "site_done"
    CONFIRM = "confirm"
    CANCEL = "cancel"
    FILTER_TOGGLE = "f_toggle"
    FILTER_DELETE = "f_delete"
    FILTER_VIEW = "f_view"
    FILTER_CLONE = "f_clone"
    CHECK_NOW = "check_now"
    MAIN_FILTERS = "main_filters"
    MAIN_ADD = "main_add"
    VAC_SAVE = "v_save"
    VAC_BLOCK = "v_block"
    VAC_SIMILAR = "v_similar"


class FilterCallback(CallbackData, prefix="fw"):
    action: WizardAction
    value: str = ""


_KW_ID: dict[str, str] = {}
_ID_KW: dict[str, str] = {}
_GROUP_ID: dict[str, str] = {}
_ID_GROUP: dict[str, str] = {}


def _build_kw_ids():
    _KW_ID.clear()
    _ID_KW.clear()
    _GROUP_ID.clear()
    _ID_GROUP.clear()
    idx = 0
    for group_idx, (group_name, group) in enumerate(KEYWORDS_BY_GROUP.items()):
        group_id = f"g{group_idx}"
        _GROUP_ID[group_name] = group_id
        _ID_GROUP[group_id] = group_name
        for display_name in group:
            sid = f"k{idx}"
            _KW_ID[display_name] = sid
            _ID_KW[sid] = display_name
            idx += 1


KEYWORDS_BY_GROUP: dict[str, dict[str, list[str]]] = {
    "1С / ERP": {
        "1С Программист": ["1С Программист", "1C Developer", "1С Разработчик", "Программист 1С"],
        "1С Аналитик": ["1С Аналитик", "1C Analyst", "Аналитик 1С"],
        "1С Консультант": ["1С Консультант", "1C Consultant", "Консультант 1С"],
        "ERP-специалист": ["ERP", "ERP-специалист", "ERP Specialist", "ERP Consultant"],
        "SAP-специалист": ["SAP", "SAP-специалист", "SAP Developer", "SAP Consultant"],
    },
    "Backend-разработка": {
        "Python-разработчик": ["Python", "Python-разработчик", "Python Developer", "Python Программист"],
        "Java-разработчик": ["Java", "Java-разработчик", "Java Developer", "Java Программист"],
        "Go-разработчик": ["Go", "Golang", "Go-разработчик", "Go Developer"],
        "C/C++ разработчик": ["C++", "C/C++", "C++ Developer", "Программист C++"],
        "C# / .NET разработчик": ["C#", ".NET", "C# Developer", ".NET Developer", "CSharp"],
        "PHP-разработчик": ["PHP", "PHP-разработчик", "PHP Developer", "Laravel"],
        "Rust-разработчик": ["Rust", "Rust Developer", "Rust-разработчик"],
        "Kotlin-разработчик (бэкенд)": ["Kotlin", "Kotlin Developer", "Kotlin-разработчик"],
        "Scala-разработчик": ["Scala", "Scala Developer", "Scala-разработчик"],
        "Ruby-разработчик": ["Ruby", "Ruby Developer", "Ruby on Rails"],
    },
    "Frontend-разработка": {
        "JavaScript / Frontend-разработчик": ["JavaScript", "JS", "Frontend", "Frontend Developer", "Frontend-разработчик"],
        "TypeScript-разработчик": ["TypeScript", "TS", "TypeScript Developer"],
        "React-разработчик": ["React", "React Developer", "ReactJS", "React-разработчик"],
        "Vue.js разработчик": ["Vue", "Vue.js", "Vue Developer", "VueJS"],
        "Angular-разработчик": ["Angular", "Angular Developer", "AngularJS"],
        "HTML / CSS верстальщик": ["HTML", "CSS", "Верстальщик", "HTML-верстальщик", "HTML/CSS"],
        "Node.js разработчик": ["Node.js", "NodeJS", "Node Developer", "Node.js разработчик"],
    },
    "Мобильная разработка": {
        "iOS-разработчик": ["iOS", "iOS Developer", "iOS-разработчик", "Swift", "Objective-C"],
        "Android-разработчик": ["Android", "Android Developer", "Android-разработчик", "Kotlin"],
        "Flutter-разработчик": ["Flutter", "Flutter Developer", "Flutter-разработчик", "Dart"],
        "React Native разработчик": ["React Native", "RN Developer", "React Native разработчик"],
    },
    "Data Science / ML / AI": {
        "Data Scientist": ["Data Scientist", "Дата-сайентист"],
        "Data Engineer": ["Data Engineer", "Data Engineering", "Инженер данных"],
        "ML Engineer": ["ML Engineer", "Machine Learning", "MLOps", "MLE"],
        "NLP-специалист": ["NLP", "Natural Language Processing", "NLP Engineer"],
        "Computer Vision специалист": ["Computer Vision", "CV Engineer", "Компьютерное зрение"],
        "AI / ИИ разработчик": ["AI", "Artificial Intelligence", "Искусственный интеллект", "ИИ", "AI Developer"],
        "BI-разработчик": ["BI Developer", "BI-разработчик", "Power BI", "Tableau"],
    },
    "Базы данных и инфраструктура": {
        "Администратор баз данных (DBA)": ["DBA", "Database Administrator", "Администратор БД"],
        "SQL-разработчик": ["SQL Developer", "SQL-разработчик", "SQL", "PL/SQL"],
        "PostgreSQL специалист": ["PostgreSQL", "Postgres DBA", "PostgreSQL Developer"],
        "MySQL/MS SQL специалист": ["MySQL", "MS SQL", "MSSQL", "SQL Server"],
        "ClickHouse / BigData": ["ClickHouse", "BigData", "Big Data", "Hadoop", "Spark"],
        "Oracle-специалист": ["Oracle", "Oracle DBA", "Oracle Developer"],
    },
    "DevOps / Cloud": {
        "DevOps-инженер": ["DevOps", "Девопс", "DevOps-инженер", "DevOps Engineer"],
        "Kubernetes / Docker": ["Kubernetes", "K8s", "Docker", "Containerization"],
        "Terraform / IaC": ["Terraform", "IaC", "Infrastructure as Code", "Packer"],
        "Ansible / Automatization": ["Ansible", "Автоматизация", "Automation Engineer"],
        "CI/CD специалист": ["CI/CD", "CI/CD Engineer", "Jenkins", "GitLab CI", "GitHub Actions"],
        "Cloud-инженер": ["Cloud", "AWS", "Azure", "GCP", "Cloud Engineer", "Облачный инженер"],
    },
    "Сети и безопасность": {
        "Сетевой инженер": ["Сетевой инженер", "Network Engineer", "Network Administrator", "Сетевик"],
        "Cisco-инженер": ["Cisco", "CCNA", "CCNP", "Cisco Engineer"],
        "Mikrotik / Сетевое администрирование": ["Mikrotik", "MikroTik", "RouterOS"],
        "Информационная безопасность": ["InfoSec", "Information Security", "Кибербезопасность", "Cybersecurity"],
        "SOC-аналитик": ["SOC", "SOC Analyst", "SIEM", "Security Operation Center"],
        "Pentest / Этичный хакер": ["Pentest", "Penetration Test", "Этичный хакер", "Ethical Hacker"],
        "DevSecOps": ["DevSecOps", "Security Engineer"],
    },
    "QA / Тестирование": {
        "QA Engineer / Тестировщик": ["QA", "QA Engineer", "Тестировщик", "Tester", "QA Manual"],
        "Automation QA": ["Automation QA", "AQA", "QA Automation", "Automation Test"],
        "Нагрузочное тестирование": ["Performance Testing", "Load Testing", "Нагрузочное тестирование", "JMeter"],
        "Тестировщик игр (Game QA)": ["Game QA", "Game Tester", "Тестировщик игр"],
        "UI/UX тестировщик": ["UI Testing", "UX Testing", "Manual Testing"],
    },
    "Управление проектами и продуктами": {
        "Project Manager": ["Project Manager", "PM", "Менеджер проектов", "Руководитель проектов"],
        "Product Manager": ["Product Manager", "Product Owner", "Продукт менеджер", "Менеджер продукта"],
        "Team Lead / Tech Lead": ["Team Lead", "Тимлид", "Tech Lead", "Engineering Manager", "Руководитель разработки"],
        "Delivery Manager": ["Delivery Manager", "Program Manager"],
        "Scrum Master / Agile": ["Scrum Master", "Agile Coach", "Scrum", "Agile"],
        "CTO / Технический директор": ["CTO", "Technical Director", "Технический директор", "CIO"],
    },
    "Дизайн": {
        "UI/UX дизайнер": ["UI/UX", "UX/UI", "UX Designer", "UI Designer", "UX/UI дизайнер"],
        "Product Designer": ["Product Designer", "Продуктовый дизайнер"],
        "Графический дизайнер": ["Графический дизайнер", "Graphic Designer", "Web Designer"],
        "Figma-дизайнер": ["Figma", "Figma Designer"],
        "Motion / Аниматор": ["Motion Designer", "Motion Graphics", "Аниматор"],
        "Гейм-дизайнер": ["Game Designer", "Гейм-дизайнер", "GameDev", "Level Designer"],
        "Арт-директор": ["Art Director", "Арт-директор", "Креативный директор"],
    },
    "Аналитика": {
        "Системный аналитик": ["System Analyst", "Системный аналитик", "Systems Analyst"],
        "Бизнес-аналитик": ["Business Analyst", "Бизнес-аналитик", "BA"],
        "Data Analyst": ["Data Analyst", "Аналитик данных"],
        "BI-аналитик": ["BI Analyst", "BI-аналитик", "Power BI", "Tableau"],
        "Продуктовый аналитик": ["Product Analyst", "Продуктовый аналитик"],
        "Web-аналитик": ["Web Analyst", "Веб-аналитик", "Google Analytics", "Яндекс Метрика"],
    },
    "Маркетинг и продажи": {
        "Маркетолог": ["Маркетолог", "Marketing Manager", "Marketer"],
        "SEO / ASO специалист": ["SEO", "SEO Specialist", "ASO", "SEO-оптимизатор"],
        "SMM / Контент-менеджер": ["SMM", "SMM Manager", "Контент-менеджер", "Content Manager"],
        "Sales Manager": ["Sales Manager", "Менеджер по продажам", "Sales"],
        "Account Manager": ["Account Manager", "Аккаунт-менеджер"],
        "Product Marketing": ["Product Marketing", "Product Marketing Manager"],
    },
    "Административный и HR": {
        "HR / Recruiter": ["HR", "HR-менеджер", "Recruiter", "Рекрутер", "HR Generalist"],
        "HRBP / HR Business Partner": ["HRBP", "HR Business Partner", "Бизнес-партнер HR"],
        "Office Manager": ["Office Manager", "Офис-менеджер", "Офис менеджер"],
        "Бухгалтер / Финансист": ["Бухгалтер", "Accountant", "Финансист", "Финансовый менеджер"],
        "Юрист / Legal": ["Юрист", "Lawyer", "Legal Counsel", "Юрисконсульт"],
        "Технический писатель": ["Technical Writer", "Tech Writer", "Технический писатель"],
        "Методолог": ["Методолог", "Methodologist"],
    },
    "Техническая поддержка": {
        "Специалист технической поддержки": ["Tech Support", "Support Engineer", "Техподдержка", "Техническая поддержка"],
        "Администратор 1С / IT": ["Администратор", "System Administrator", "СисАдмин", "SysAdmin"],
        "DevOps / SRE": ["SRE", "Site Reliability Engineer", "DevOps"],
    },
}

_build_kw_ids()

CITIES: dict[str, str] = {
    "moscow": "Москва",
    "spb": "Санкт-Петербург",
    "kazan": "Казань",
    "novosibirsk": "Новосибирск",
    "ekb": "Екатеринбург",
    "krasnodar": "Краснодар",
    "nnovgorod": "Нижний Новгород",
    "rostov": "Ростов-на-Дону",
}

EXPERIENCE: dict[str, str] = {
    "no": "Без опыта",
    "1-3": "1–3 года",
    "3-6": "3–6 лет",
    "6+": "Более 6 лет",
}

SALARIES: list[tuple[str, str, int | None, int | None]] = [
    ("any", "Любая", None, None),
    ("0-100", "до 100 000 ₽", None, 100_000),
    ("100-200", "100 000 – 200 000 ₽", 100_000, 200_000),
    ("200-300", "200 000 – 300 000 ₽", 200_000, 300_000),
    ("300-500", "300 000 – 500 000 ₽", 300_000, 500_000),
    ("500-0", "от 500 000 ₽", 500_000, None),
    ("custom", "🖊 Своя сумма", None, None),
]

EMPLOYMENT_TYPES: dict[str, str] = {
    "full": "Полная",
    "part": "Частичная",
    "remote": "Удалённо",
    "project": "Проектная",
    "internship": "Стажировка",
}

SITES: dict[str, str] = {
    "hh": "hh.ru",
    "superjob": "SuperJob",
    "rabota": "rabota.ru",
    "habr": "Хабр Карьера",
    "trudvsem": "Работа России",
}


def get_synonyms(display_names: list[str]) -> list[str]:
    """Convert display names to all search synonyms for API queries.
    Also matches any keyword to its synonym group (e.g., 'SysAdmin' -> all Russian forms)."""
    lookup: dict[str, list[str]] = {}
    for group in KEYWORDS_BY_GROUP.values():
        for display, syns in group.items():
            lookup[display] = syns
            for s in syns:
                if s not in lookup:
                    lookup[s] = syns

    result: list[str] = []
    for name in display_names:
        if name in lookup:
            result.extend(lookup[name])
        else:
            result.append(name)
    return list(dict.fromkeys(result))


def _btn(text: str, action: WizardAction, value: str = "") -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=text,
        callback_data=FilterCallback(action=action, value=value).pack(),
    )


def build_start_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        _btn("➕ Добавить фильтр", WizardAction.MAIN_ADD),
        _btn("📋 Мои фильтры", WizardAction.MAIN_FILTERS),
    )
    builder.row(_btn("🔎 Проверить сейчас", WizardAction.CHECK_NOW))
    return builder.as_markup()


def _build_keyword_grid(
    selected: list[str], toggle_action: WizardAction, done_action: WizardAction,
    title: str, back_action: WizardAction | None = None,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    # Navigation at top so users can proceed without scrolling through all keywords
    top_row = []
    if back_action:
        top_row.append(_btn("⬅️ Назад", back_action))
    top_row.append(_btn(f"✅ {title}", done_action))
    builder.row(*top_row)
    for group_name, kw_dict in KEYWORDS_BY_GROUP.items():
        builder.row(
            InlineKeyboardButton(
                text=f"— {group_name} —",
                callback_data=FilterCallback(action=WizardAction.NOOP, value="").pack(),
            )
        )
        row_buttons = []
        for display_name in kw_dict:
            text = f"🚫 {display_name}" if display_name in selected else display_name
            if toggle_action == WizardAction.KEYWORD_TOGGLE:
                text = f"✅ {display_name}" if display_name in selected else display_name
            row_buttons.append(
                InlineKeyboardButton(
                    text=text,
                    callback_data=FilterCallback(action=toggle_action, value=_KW_ID.get(display_name, display_name)).pack(),
                )
            )
        for i in range(0, len(row_buttons), 4):
            builder.row(*row_buttons[i:i + 4])
    nav_row = []
    if back_action:
        nav_row.append(_btn("⬅️ Назад", back_action))
    nav_row.append(_btn(f"✅ {title}", done_action))
    builder.row(*nav_row)
    builder.row(_btn("❌ Отмена", WizardAction.CANCEL))
    return builder.as_markup()


def build_keyword_groups_keyboard(selected: list[str] | None = None) -> InlineKeyboardMarkup:
    """First step: show 15 groups, user picks one to see keywords."""
    selected = selected or []
    cnt = len(selected)
    done_label = f"✅ Готово ({cnt} выбрано)" if cnt else "✅ Далее"
    builder = InlineKeyboardBuilder()
    for group_name in KEYWORDS_BY_GROUP:
        has_sel = any(s in KEYWORDS_BY_GROUP[group_name] for s in selected)
        label = f"✅ {group_name}" if has_sel else group_name
        builder.row(InlineKeyboardButton(
            text=label,
            callback_data=FilterCallback(action=WizardAction.KW_GROUP_SELECT, value=_GROUP_ID[group_name]).pack(),
        ))
    builder.row(_btn(done_label, WizardAction.KEYWORD_DONE, value="__done__"))
    builder.row(_btn("❌ Отмена", WizardAction.CANCEL))
    return builder.as_markup()


def build_keywords_for_group_keyboard(group: str, selected: list[str]) -> InlineKeyboardMarkup:
    """Second step: show keywords for ONE selected group + nav."""
    builder = InlineKeyboardBuilder()
    kw_dict = KEYWORDS_BY_GROUP.get(group, {})
    # Top nav
    builder.row(_btn("⬅️ Назад к группам", WizardAction.KW_GROUP_BACK))
    cnt = sum(1 for s in selected if s in kw_dict)
    builder.row(_btn(f"✅ Далее → ({cnt} выбрано)", WizardAction.KEYWORD_DONE, value="__done__"))
    # Keywords
    row_buttons = []
    for display_name in kw_dict:
        text = f"✅ {display_name}" if display_name in selected else display_name
        row_buttons.append(InlineKeyboardButton(
            text=text,
            callback_data=FilterCallback(action=WizardAction.KEYWORD_TOGGLE, value=_KW_ID.get(display_name, display_name)).pack(),
        ))
    for i in range(0, len(row_buttons), 4):
        builder.row(*row_buttons[i:i + 4])
    # Bottom nav
    builder.row(_btn(f"✅ Далее → ({cnt} выбрано)", WizardAction.KEYWORD_DONE, value="__done__"))
    builder.row(_btn("⬅️ Назад к группам", WizardAction.KW_GROUP_BACK))
    builder.row(_btn("❌ Отмена", WizardAction.CANCEL))
    return builder.as_markup()



def build_exclude_keywords_keyboard(selected: list[str]) -> InlineKeyboardMarkup:
    return _build_keyword_grid(
        selected, WizardAction.EXCLUDE_TOGGLE, WizardAction.EXCLUDE_DONE,
        "Р”Р°Р»РµРµ в†’", back_action=WizardAction.KW_GROUP_BACK,
    )


def build_city_keyboard(selected: str | None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    row_buttons = []
    for key, label in CITIES.items():
        text = f"✅ {label}" if key == selected else label
        row_buttons.append(
            InlineKeyboardButton(
                text=text,
                callback_data=FilterCallback(action=WizardAction.CITY_SELECT, value=key).pack(),
            )
        )
    for i in range(0, len(row_buttons), 3):
        builder.row(*row_buttons[i:i + 3])
    is_any = selected is None
    builder.row(_btn("🌍 Любой (все города)" if not is_any else "✅ Любой (все города)", WizardAction.CITY_SELECT, value="any"))
    builder.row(
        _btn("⬅️ Назад", WizardAction.EXCLUDE_DONE, value="__back__"),
        _btn("✅ Далее →", WizardAction.CITY_DONE_SKIP, value="__done__"),
    )
    builder.row(_btn("❌ Отмена", WizardAction.CANCEL))
    return builder.as_markup()


def build_experience_keyboard(selected: str | None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, label in EXPERIENCE.items():
        text = f"✅ {label}" if key == selected else label
        builder.row(
            InlineKeyboardButton(
                text=text,
                callback_data=FilterCallback(action=WizardAction.EXPERIENCE_SELECT, value=key).pack(),
            )
        )
    builder.row(
        _btn("⬅️ Назад", WizardAction.EXPERIENCE_SELECT, value="__back__"),
        _btn("✅ Далее →", WizardAction.EXPERIENCE_SELECT, value="__done__"),
    )
    builder.row(_btn("❌ Отмена", WizardAction.CANCEL))
    return builder.as_markup()


def build_salary_keyboard(selected_key: str | None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, label, _, _ in SALARIES:
        text = f"✅ {label}" if key == selected_key else label
        builder.row(
            InlineKeyboardButton(
                text=text,
                callback_data=FilterCallback(action=WizardAction.SALARY_SELECT, value=key).pack(),
            )
        )
    builder.row(
        _btn("⬅️ Назад", WizardAction.SALARY_SELECT, value="__back__"),
        _btn("✅ Далее →", WizardAction.SALARY_SELECT, value="__done__"),
    )
    builder.row(_btn("❌ Отмена", WizardAction.CANCEL))
    return builder.as_markup()


def build_employment_keyboard(selected: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, label in EMPLOYMENT_TYPES.items():
        text = f"✅ {label}" if key in selected else label
        builder.row(
            InlineKeyboardButton(
                text=text,
                callback_data=FilterCallback(action=WizardAction.EMPLOYMENT_TOGGLE, value=key).pack(),
            )
        )
    builder.row(
        _btn("⬅️ Назад", WizardAction.EMPLOYMENT_DONE, value="__back__"),
        _btn("✅ Далее →", WizardAction.EMPLOYMENT_DONE, value="__done__"),
    )
    builder.row(_btn("❌ Отмена", WizardAction.CANCEL))
    return builder.as_markup()


def build_sites_keyboard(selected: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, label in SITES.items():
        text = f"✅ {label}" if key in selected else label
        builder.row(
            InlineKeyboardButton(
                text=text,
                callback_data=FilterCallback(action=WizardAction.SITE_TOGGLE, value=key).pack(),
            )
        )
    builder.row(
        _btn("⬅️ Назад", WizardAction.SITE_DONE, value="__back__"),
        _btn("✅ Готово!", WizardAction.SITE_DONE, value="__done__"),
    )
    builder.row(_btn("❌ Отмена", WizardAction.CANCEL))
    return builder.as_markup()


def build_confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        _btn("✅ Создать фильтр", WizardAction.CONFIRM),
        _btn("❌ Отмена", WizardAction.CANCEL),
    )
    return builder.as_markup()


def build_filters_list_keyboard(filters: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for vf in filters:
        status = "🟢" if vf.active else "🔴"
        builder.row(
            InlineKeyboardButton(
                text=f"{status} {vf.name}",
                callback_data=FilterCallback(action=WizardAction.FILTER_VIEW, value=str(vf.id)).pack(),
            ),
            _btn("⏸" if vf.active else "▶️", WizardAction.FILTER_TOGGLE, str(vf.id)),
            _btn("🗑", WizardAction.FILTER_DELETE, str(vf.id)),
        )
    builder.row(_btn("➕ Добавить фильтр", WizardAction.MAIN_ADD))
    builder.row(_btn("🔎 Проверить сейчас", WizardAction.CHECK_NOW))
    return builder.as_markup()


def build_vacancy_actions_keyboard(
    vacancy_id: int, source: str, url: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if url:
        builder.row(
            InlineKeyboardButton(text="🔗 Открыть вакансию", url=url),
        )
    builder.row(
        _btn("⭐ Сохранить", WizardAction.VAC_SAVE, str(vacancy_id)),
        _btn("🙈 Скрыть", WizardAction.VAC_BLOCK, f"{vacancy_id}|{source}"),
        _btn("🧭 Похожие", WizardAction.VAC_SIMILAR, str(vacancy_id)),
    )
    return builder.as_markup()


def build_filter_detail_keyboard(filter_id: int, is_active: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        _btn("📄 Клонировать", WizardAction.FILTER_CLONE, str(filter_id)),
        _btn("⏸" if is_active else "▶️", WizardAction.FILTER_TOGGLE, str(filter_id)),
    )
    builder.row(
        _btn("🗑 Удалить", WizardAction.FILTER_DELETE, str(filter_id)),
        _btn("◀️ Назад", WizardAction.MAIN_FILTERS),
    )
    return builder.as_markup()


