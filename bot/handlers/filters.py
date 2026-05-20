from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.keyboards import (
    FilterCallback, WizardAction,
    build_keywords_keyboard, build_exclude_keywords_keyboard,
    build_city_keyboard, build_salary_keyboard,
    build_employment_keyboard, build_sites_keyboard,
    build_confirm_keyboard, build_start_keyboard,
    build_filters_list_keyboard,
    SALARIES, EMPLOYMENT_TYPES, SITES,
)
from core.database.repository import Database

router = Router()


class FilterWizard(StatesGroup):
    keywords = State()
    exclude_keywords = State()
    city = State()
    salary = State()
    employment = State()
    sites = State()
    confirm = State()


@router.message(Command("add_filter"))
async def cmd_add_filter(message: Message, state: FSMContext):
    await state.update_data(
        selected_keywords=[],
        excluded_keywords=[],
        city=None,
        salary_key=None,
        salary_min=None,
        salary_max=None,
        employment_types=[],
        sites=[],
    )
    await state.set_state(FilterWizard.keywords)
    await message.answer(
        "Шаг 1 — Выбери ключевые слова для поиска\n\n"
        "Нажимай на слова, чтобы добавить их в фильтр.\n"
        "Можно выбрать несколько из разных групп.",
        reply_markup=build_keywords_keyboard([]),
    )


@router.callback_query(FilterCallback.filter(F.action == WizardAction.KEYWORD_TOGGLE))
async def on_keyword_toggle(callback: CallbackQuery, state: FSMContext):
    kw = FilterCallback.unpack(callback.data).value
    data = await state.get_data()
    selected: list[str] = data.get("selected_keywords", [])
    if kw in selected:
        selected.remove(kw)
    else:
        selected.append(kw)
    await state.update_data(selected_keywords=selected)
    await callback.message.edit_reply_markup(reply_markup=build_keywords_keyboard(selected))
    await callback.answer()


@router.callback_query(FilterCallback.filter(F.action == WizardAction.NOOP))
async def on_noop(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(FilterCallback.filter(F.action == WizardAction.CANCEL))
async def on_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ Создание фильтра отменено.",
        reply_markup=build_start_keyboard(),
    )
    await callback.answer()


@router.callback_query(FilterCallback.filter(F.action == WizardAction.KEYWORD_DONE))
async def on_keyword_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("selected_keywords", [])
    if not selected:
        await callback.answer("Выбери хотя бы одно ключевое слово!", show_alert=True)
        return
    await state.set_state(FilterWizard.exclude_keywords)
    excluded = data.get("excluded_keywords", [])
    await callback.message.edit_text(
        "Шаг 2 — Выбери слова, которые нужно ИСКЛЮЧИТЬ\n\n"
        "Если хочешь исключить какие-то технологии или роли, отметь их.\n"
        "Если нет — просто нажми «Далее».",
        reply_markup=build_exclude_keywords_keyboard(excluded),
    )
    await callback.answer()


@router.callback_query(FilterCallback.filter(F.action == WizardAction.EXCLUDE_TOGGLE))
async def on_exclude_toggle(callback: CallbackQuery, state: FSMContext):
    kw = FilterCallback.unpack(callback.data).value
    data = await state.get_data()
    excluded: list[str] = data.get("excluded_keywords", [])
    if kw in excluded:
        excluded.remove(kw)
    else:
        excluded.append(kw)
    await state.update_data(excluded_keywords=excluded)
    await callback.message.edit_reply_markup(
        reply_markup=build_exclude_keywords_keyboard(excluded)
    )
    await callback.answer()


@router.callback_query(FilterCallback.filter(F.action == WizardAction.EXCLUDE_DONE))
async def on_exclude_done(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FilterWizard.city)
    data = await state.get_data()
    city = data.get("city", None)
    await callback.message.edit_text(
        "Шаг 3 — Выбери город\n\n"
        "Если город не важен, нажми «Любой».",
        reply_markup=build_city_keyboard(city),
    )
    await callback.answer()


@router.callback_query(FilterCallback.filter(F.action == WizardAction.CITY_SELECT))
async def on_city_select(callback: CallbackQuery, state: FSMContext):
    value = FilterCallback.unpack(callback.data).value
    if value == "__done__":
        await on_city_done(callback, state)
        return
    await state.update_data(city=value if value != "any" else None)
    await callback.message.edit_reply_markup(
        reply_markup=build_city_keyboard(value)
    )
    await callback.answer()


async def on_city_done(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FilterWizard.salary)
    data = await state.get_data()
    salary_key = data.get("salary_key", None)
    await callback.message.edit_text(
        "Шаг 4 — Выбери диапазон зарплаты",
        reply_markup=build_salary_keyboard(salary_key),
    )
    await callback.answer()


@router.callback_query(FilterCallback.filter(F.action == WizardAction.SALARY_SELECT))
async def on_salary_select(callback: CallbackQuery, state: FSMContext):
    value = FilterCallback.unpack(callback.data).value
    if value == "__done__":
        await on_salary_done(callback, state)
        return
    if value == "__back__":
        data = await state.get_data()
        city = data.get("city", None)
        await state.set_state(FilterWizard.city)
        await callback.message.edit_text(
            "Шаг 3 — Выбери город",
            reply_markup=build_city_keyboard(city),
        )
        await callback.answer()
        return

    salary_min, salary_max = None, None
    for key, _, smin, smax in SALARIES:
        if key == value:
            salary_min = smin
            salary_max = smax
            break
    await state.update_data(salary_key=value, salary_min=salary_min, salary_max=salary_max)
    await callback.message.edit_reply_markup(
        reply_markup=build_salary_keyboard(value)
    )
    await callback.answer()


async def on_salary_done(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FilterWizard.employment)
    data = await state.get_data()
    emp_types = data.get("employment_types", [])
    await callback.message.edit_text(
        "Шаг 5 — Выбери тип занятости\n\n"
        "Можно выбрать несколько вариантов.",
        reply_markup=build_employment_keyboard(emp_types),
    )
    await callback.answer()


@router.callback_query(FilterCallback.filter(F.action == WizardAction.EMPLOYMENT_TOGGLE))
async def on_employment_toggle(callback: CallbackQuery, state: FSMContext):
    value = FilterCallback.unpack(callback.data).value
    data = await state.get_data()
    emp_types: list[str] = data.get("employment_types", [])
    if value in emp_types:
        emp_types.remove(value)
    else:
        emp_types.append(value)
    await state.update_data(employment_types=emp_types)
    await callback.message.edit_reply_markup(
        reply_markup=build_employment_keyboard(emp_types)
    )
    await callback.answer()


@router.callback_query(FilterCallback.filter(F.action == WizardAction.EMPLOYMENT_DONE))
async def on_employment_done(callback: CallbackQuery, state: FSMContext):
    value = FilterCallback.unpack(callback.data).value
    if value == "__back__":
        data = await state.get_data()
        salary_key = data.get("salary_key", None)
        await state.set_state(FilterWizard.salary)
        await callback.message.edit_text(
            "Шаг 4 — Выбери диапазон зарплаты",
            reply_markup=build_salary_keyboard(salary_key),
        )
        await callback.answer()
        return
    await state.set_state(FilterWizard.sites)
    data = await state.get_data()
    sites = data.get("sites", [])
    await callback.message.edit_text(
        "Шаг 6 — Выбери сайты для поиска\n\n"
        "Можно выбрать несколько.",
        reply_markup=build_sites_keyboard(sites),
    )
    await callback.answer()


@router.callback_query(FilterCallback.filter(F.action == WizardAction.SITE_TOGGLE))
async def on_site_toggle(callback: CallbackQuery, state: FSMContext):
    value = FilterCallback.unpack(callback.data).value
    data = await state.get_data()
    sites: list[str] = data.get("sites", [])
    if value in sites:
        sites.remove(value)
    else:
        sites.append(value)
    await state.update_data(sites=sites)
    await callback.message.edit_reply_markup(
        reply_markup=build_sites_keyboard(sites)
    )
    await callback.answer()


@router.callback_query(FilterCallback.filter(F.action == WizardAction.SITE_DONE))
async def on_site_done(callback: CallbackQuery, state: FSMContext):
    value = FilterCallback.unpack(callback.data).value
    if value == "__back__":
        data = await state.get_data()
        emp_types = data.get("employment_types", [])
        await state.set_state(FilterWizard.employment)
        await callback.message.edit_text(
            "Шаг 5 — Выбери тип занятости",
            reply_markup=build_employment_keyboard(emp_types),
        )
        await callback.answer()
        return
    data = await state.get_data()
    sites: list[str] = data.get("sites", [])
    if not sites:
        await callback.answer("Выбери хотя бы один сайт!", show_alert=True)
        return

    kws = data.get("selected_keywords", [])
    name_parts = kws[:3]
    salary_key = data.get("salary_key")
    if salary_key and salary_key != "any":
        for key, label, _, _ in SALARIES:
            if key == salary_key:
                name_parts.append(label)
                break
    name = " ".join(name_parts) if name_parts else "Мой фильтр"

    await state.update_data(filter_name=name)
    await state.set_state(FilterWizard.confirm)

    lines = [f"📋 <b>Имя:</b> {name}"]
    lines.append(f"<b>Ключевые слова:</b> {', '.join(kws)}")
    excluded = data.get("excluded_keywords", [])
    if excluded:
        lines.append(f"<b>Исключить:</b> {', '.join(excluded)}")
    city = data.get("city")
    lines.append(f"<b>Город:</b> {city or 'Любой'}")
    if data.get("salary_min") is not None or data.get("salary_max") is not None:
        parts = []
        if data.get("salary_min"):
            parts.append(f"от {data['salary_min']:,}".replace(",", " "))
        if data.get("salary_max"):
            parts.append(f"до {data['salary_max']:,}".replace(",", " "))
        lines.append(f"<b>Зарплата:</b> {' '.join(parts)} ₽")
    else:
        lines.append("<b>Зарплата:</b> Любая")
    emp_labels = [EMPLOYMENT_TYPES.get(e, e) for e in data.get("employment_types", [])]
    lines.append(f"<b>Тип занятости:</b> {', '.join(emp_labels) or 'Любой'}")
    site_labels = [SITES.get(s, s) for s in sites]
    lines.append(f"<b>Сайты:</b> {', '.join(site_labels)}")

    await callback.message.edit_text(
        "\n".join(lines) + "\n\nСоздать этот фильтр?",
        reply_markup=build_confirm_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(FilterCallback.filter(F.action == WizardAction.CONFIRM))
async def on_confirm(callback: CallbackQuery, state: FSMContext, db: Database):
    data = await state.get_data()
    user = await db.get_or_create_user(callback.from_user.id)
    vf = await db.create_filter(
        user_id=user.id,
        name=data["filter_name"],
        keywords=data["selected_keywords"],
        city=data["city"],
        salary_min=data["salary_min"],
        salary_max=data["salary_max"],
        employment_types=data["employment_types"],
        sites=data["sites"],
        exclude_keywords=data.get("excluded_keywords", []),
    )
    await state.clear()
    await callback.message.edit_text(
        f"✅ Фильтр «{vf.name}» создан!\n\n"
        f"Теперь я буду присылать подходящие вакансии раз в час.",
        reply_markup=build_start_keyboard(),
    )
    await callback.answer()
