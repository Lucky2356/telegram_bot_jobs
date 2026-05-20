from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton, InlineKeyboardMarkup
from enum import StrEnum


class WizardAction(StrEnum):
    NOOP = "noop"
    KEYWORD_TOGGLE = "kw"
    KEYWORD_DONE = "kw_done"
    CITY_SELECT = "city"
    SALARY_SELECT = "sal"
    EMPLOYMENT_TOGGLE = "emp"
    EMPLOYMENT_DONE = "emp_done"
    SITE_TOGGLE = "site"
    SITE_DONE = "site_done"
    CONFIRM = "confirm"
    CANCEL = "cancel"
    FILTER_TOGGLE = "f_toggle"
    FILTER_DELETE = "f_delete"
    CHECK_NOW = "check_now"
    MAIN_FILTERS = "main_filters"
    MAIN_ADD = "main_add"


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

SALARIES: list[tuple[str, str, int | None, int | None]] = [
    ("any", "Любая", None, None),
    ("0-100", "до 100 000 ₽", None, 100_000),
    ("100-200", "100 000 – 200 000 ₽", 100_000, 200_000),
    ("200-300", "200 000 – 300 000 ₽", 200_000, 300_000),
    ("300-500", "300 000 – 500 000 ₽", 300_000, 500_000),
    ("500-0", "от 500 000 ₽", 500_000, None),
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


def build_keywords_keyboard(selected: list[str]) -> InlineKeyboardMarkup:
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
            text = f"✅ {kw}" if kw in selected else kw
            row_buttons.append(
                InlineKeyboardButton(
                    text=text,
                    callback_data=FilterCallback(action=WizardAction.KEYWORD_TOGGLE, value=kw).pack(),
                )
            )
        for i in range(0, len(row_buttons), 4):
            builder.row(*row_buttons[i:i + 4])
    builder.row(
        _btn("✅ Далее →", WizardAction.KEYWORD_DONE),
    )
    builder.row(_btn("❌ Отмена", WizardAction.CANCEL))
    return builder.as_markup()


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
        _btn("⬅️ Назад", WizardAction.KEYWORD_DONE),
        _btn("✅ Далее →", WizardAction.SALARY_SELECT, value="__done__"),
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
        _btn("⬅️ Назад", WizardAction.CITY_SELECT, value="__back__"),
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


def build_filters_list_keyboard(
    filters: list,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for vf in filters:
        status = "🟢" if vf.active else "🔴"
        builder.row(
            InlineKeyboardButton(
                text=f"{status} {vf.name}",
                callback_data=FilterCallback(action=WizardAction.NOOP, value="").pack(),
            ),
            _btn("⏸" if vf.active else "▶️", WizardAction.FILTER_TOGGLE, str(vf.id)),
            _btn("🗑", WizardAction.FILTER_DELETE, str(vf.id)),
        )
    builder.row(_btn("➕ Добавить фильтр", WizardAction.MAIN_ADD))
    builder.row(_btn("🔍 Проверить сейчас", WizardAction.CHECK_NOW))
    return builder.as_markup()
