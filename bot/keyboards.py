from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton, InlineKeyboardMarkup
from enum import StrEnum


class WizardAction(StrEnum):
    NOOP = "noop"
    KEYWORD_TOGGLE = "kw"
    KEYWORD_DONE = "kw_done"
    EXCLUDE_TOGGLE = "ex_kw"
    EXCLUDE_DONE = "ex_done"
    CITY_SELECT = "city"
    CITY_DONE_SKIP = "city_done"
    EXPERIENCE_SELECT = "exp"
    EXPERIENCE_DONE = "exp_done"
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


KEYWORDS_BY_GROUP: dict[str, list[str]] = {
    "Языки": ["Python", "JavaScript", "TypeScript", "Go", "Java", "C++", "C#", "Rust", "PHP", "Ruby", "Kotlin", "Swift"],
    "Роли": ["Backend", "Frontend", "Fullstack", "DevOps", "Data Science", "ML Engineer", "QA", "iOS", "Android", "Аналитик", "Дизайнер", "PM", "SysAdmin"],
    "Сеньорити": ["Junior", "Middle", "Senior", "Lead"],
    "Домен": ["Fintech", "E-commerce", "EdTech", "GameDev", "Маркетинг", "Медицина", "ERP"],
}

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
    builder.row(_btn("🔍 Проверить сейчас", WizardAction.CHECK_NOW))
    return builder.as_markup()


def _build_keyword_grid(
    selected: list[str], toggle_action: WizardAction, done_action: WizardAction,
    title: str, back_action: WizardAction | None = None,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for group_name, keywords in KEYWORDS_BY_GROUP.items():
        builder.row(
            InlineKeyboardButton(
                text=f"— {group_name} —",
                callback_data=FilterCallback(action=WizardAction.NOOP, value="").pack(),
            )
        )
        row_buttons = []
        for kw in keywords:
            text = f"🚫 {kw}" if kw in selected else kw
            if toggle_action == WizardAction.KEYWORD_TOGGLE:
                text = f"✅ {kw}" if kw in selected else kw
            row_buttons.append(
                InlineKeyboardButton(
                    text=text,
                    callback_data=FilterCallback(action=toggle_action, value=kw).pack(),
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


def build_keywords_keyboard(selected: list[str]) -> InlineKeyboardMarkup:
    return _build_keyword_grid(
        selected, WizardAction.KEYWORD_TOGGLE, WizardAction.KEYWORD_DONE,
        "Далее →",
    )


def build_exclude_keywords_keyboard(selected: list[str]) -> InlineKeyboardMarkup:
    return _build_keyword_grid(
        selected, WizardAction.EXCLUDE_TOGGLE, WizardAction.EXCLUDE_DONE,
        "Далее →", back_action=WizardAction.KEYWORD_DONE,
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
    builder.row(_btn("🌍 Любой (все города)", WizardAction.CITY_SELECT, value="any"))
    builder.row(
        _btn("⬅️ Назад", WizardAction.EXCLUDE_DONE),
        _btn("✅ Далее →", WizardAction.EXPERIENCE_DONE, value="__done__"),
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
        _btn("⬅️ Назад", WizardAction.CITY_SELECT, value="__back__"),
        _btn("✅ Далее →", WizardAction.EXPERIENCE_DONE, value="__done__"),
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
        _btn("⬅️ Назад", WizardAction.EXPERIENCE_DONE, value="__back__"),
        _btn("✅ Далее →", WizardAction.EMPLOYMENT_DONE, value="__done__"),
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
        _btn("⬅️ Назад", WizardAction.SALARY_SELECT, value="__back__"),
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
        _btn("⬅️ Назад", WizardAction.EMPLOYMENT_DONE, value="__back__"),
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
    builder.row(_btn("🔍 Проверить сейчас", WizardAction.CHECK_NOW))
    return builder.as_markup()


def build_vacancy_actions_keyboard(
    vacancy_id: int, source: str, url: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔗 Открыть", url=url),
    )
    builder.row(
        _btn("📌 Отложить", WizardAction.VAC_SAVE, str(vacancy_id)),
        _btn("🚫 Не интересует", WizardAction.VAC_BLOCK, f"{vacancy_id}:{source}"),
        _btn("🔍 Похожие", WizardAction.VAC_SIMILAR, str(vacancy_id)),
    )
    return builder.as_markup()


def build_filter_detail_keyboard(filter_id: int, is_active: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        _btn("📋 Клонировать", WizardAction.FILTER_CLONE, str(filter_id)),
        _btn("⏸" if is_active else "▶️", WizardAction.FILTER_TOGGLE, str(filter_id)),
    )
    builder.row(
        _btn("🗑 Удалить", WizardAction.FILTER_DELETE, str(filter_id)),
        _btn("◀️ Назад", WizardAction.MAIN_FILTERS),
    )
    return builder.as_markup()
