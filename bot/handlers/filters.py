from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest
from html import escape
from bot.keyboards import (
    FilterCallback, WizardAction,
    build_keyword_groups_keyboard,
    build_keywords_for_group_keyboard,
    build_exclude_keywords_keyboard,
    build_city_keyboard, build_experience_keyboard,
    build_salary_keyboard,
    build_employment_keyboard, build_sites_keyboard,
    build_confirm_keyboard, build_start_keyboard,
    build_filters_list_keyboard,
    SALARIES, EXPERIENCE, EMPLOYMENT_TYPES, SITES, KEYWORDS_BY_GROUP,
    _ID_KW, _ID_GROUP,
)
from core.database.repository import Database

router = Router()


def _h(value) -> str:
    return escape("" if value is None else str(value), quote=False)


async def _safe_edit(msg, text=None, reply_markup=None, **kwargs):
    try:
        if text is not None:
            await msg.edit_text(text=text, reply_markup=reply_markup, **kwargs)
        elif reply_markup is not None:
            await msg.edit_reply_markup(reply_markup=reply_markup)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            raise


class FilterWizard(StatesGroup):
    keywords = State()
    exclude_keywords = State()
    city = State()
    experience = State()
    salary = State()
    custom_salary = State()
    employment = State()
    sites = State()
    confirm = State()


@router.message(Command("add_filter"))
async def cmd_add_filter(message: Message, state: FSMContext):
    await state.update_data(
        selected_keywords=[],
        excluded_keywords=[],
        experience=None,
        city=None,
        salary_key=None,
        salary_min=None,
        salary_max=None,
        employment_types=[],
        sites=list(SITES.keys()),
    )
    await state.set_state(FilterWizard.keywords)
    await message.answer(
        "Шаг 1 — Выбери категорию ключевых слов\n\n"
        "Нажми на категорию, чтобы увидеть слова внутри.\n"
        "Можно выбрать слова из нескольких категорий.",
        reply_markup=build_keyword_groups_keyboard(),
    )


@router.callback_query(FilterCallback.filter(F.action == WizardAction.KW_GROUP_SELECT))
async def on_keyword_group_select(callback: CallbackQuery, state: FSMContext):
    group_id = FilterCallback.unpack(callback.data).value
    group = _ID_GROUP.get(group_id, group_id)
    data = await state.get_data()
    selected: list[str] = data.get("selected_keywords", [])
    await state.update_data(current_group=group)
    await _safe_edit(callback.message, text=f"📁 {group}\n\nНажимай на слова, чтобы добавить их в фильтр.",
        reply_markup=build_keywords_for_group_keyboard(group, selected),
    )
    await callback.answer()


@router.callback_query(FilterCallback.filter(F.action == WizardAction.KW_GROUP_BACK))
async def on_keyword_group_back(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FilterWizard.keywords)
    data = await state.get_data()
    selected: list[str] = data.get("selected_keywords", [])
    cnt = len(selected)
    text = "Шаг 1 — Выбери категорию ключевых слов\n\n"
    if cnt:
        text += f"✅ Выбрано {cnt} слов. Можешь добавить ещё из других категорий."
    else:
        text += "Нажми на категорию, чтобы увидеть слова внутри."
    await _safe_edit(callback.message, text=text,
        reply_markup=build_keyword_groups_keyboard(selected),
    )
    await callback.answer()


@router.callback_query(FilterCallback.filter(F.action == WizardAction.KEYWORD_TOGGLE))
async def on_keyword_toggle(callback: CallbackQuery, state: FSMContext):
    kw_id = FilterCallback.unpack(callback.data).value
    kw = _ID_KW.get(kw_id, kw_id)
    data = await state.get_data()
    selected: list[str] = data.get("selected_keywords", [])
    if kw in selected:
        selected.remove(kw)
        await callback.answer(f"🚫 {kw} убрано")
    else:
        selected.append(kw)
        await callback.answer(f"✅ {kw} добавлено")
    await state.update_data(selected_keywords=selected)
    current_group = data.get("current_group")
    if current_group:
        await _safe_edit(callback.message, reply_markup=build_keywords_for_group_keyboard(current_group, selected))


@router.callback_query(FilterCallback.filter(F.action == WizardAction.NOOP))
async def on_noop(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(FilterCallback.filter(F.action == WizardAction.CANCEL))
async def on_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await _safe_edit(callback.message, text="❌ Создание фильтра отменено.",
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
    await _safe_edit(callback.message, text="Выбери слова, которые нужно ИСКЛЮЧИТЬ\n\n"
        "Если хочешь исключить какие-то технологии или роли, отметь их.\n"
        "Если нет — просто нажми «Далее».",
        reply_markup=build_exclude_keywords_keyboard(excluded),
    )
    await callback.answer(f"✅ Выбрано {len(selected)} слов")


@router.callback_query(FilterCallback.filter(F.action == WizardAction.EXCLUDE_TOGGLE))
async def on_exclude_toggle(callback: CallbackQuery, state: FSMContext):
    kw_id = FilterCallback.unpack(callback.data).value
    kw = _ID_KW.get(kw_id, kw_id)
    data = await state.get_data()
    excluded: list[str] = data.get("excluded_keywords", [])
    if kw in excluded:
        excluded.remove(kw)
    else:
        excluded.append(kw)
    await state.update_data(excluded_keywords=excluded)
    await _safe_edit(callback.message, reply_markup=build_exclude_keywords_keyboard(excluded))
    action = "🚫 исключено" if kw in excluded else "✅ исключено"
    await callback.answer(action)


@router.callback_query(FilterCallback.filter(F.action == WizardAction.EXCLUDE_DONE))
async def on_exclude_done(callback: CallbackQuery, state: FSMContext):
    value = FilterCallback.unpack(callback.data).value
    if value == "__back__":
        data = await state.get_data()
        excluded = data.get("excluded_keywords", [])
        await state.set_state(FilterWizard.exclude_keywords)
        await _safe_edit(callback.message, text="Выбери слова, которые нужно ИСКЛЮЧИТЬ\n\n"
            "Если хочешь исключить какие-то технологии или роли, отметь их.\n"
            "Если нет — просто нажми «Далее».",
            reply_markup=build_exclude_keywords_keyboard(excluded),
        )
        await callback.answer()
        return
    await state.set_state(FilterWizard.city)
    data = await state.get_data()
    city = data.get("city", None)
    await _safe_edit(callback.message, text="Выбери город\n\n"
        "Если город не важен, нажми «Любой».",
        reply_markup=build_city_keyboard(city),
    )
    await callback.answer()


@router.callback_query(FilterCallback.filter(F.action == WizardAction.CITY_SELECT))
async def on_city_select(callback: CallbackQuery, state: FSMContext):
    value = FilterCallback.unpack(callback.data).value
    if value == "__back__":
        await state.set_state(FilterWizard.exclude_keywords)
        data = await state.get_data()
        excluded = data.get("excluded_keywords", [])
        await _safe_edit(callback.message, text="Выбери слова, которые нужно ИСКЛЮЧИТЬ\n\n"
            "Если хочешь исключить какие-то технологии или роли, отметь их.\n"
            "Если нет — просто нажми «Далее».",
            reply_markup=build_exclude_keywords_keyboard(excluded),
        )
        await callback.answer()
        return
    await state.update_data(city=None if value == "any" else value)
    await _safe_edit(callback.message, reply_markup=build_city_keyboard(None if value == "any" else value)
    )
    await callback.answer()


@router.callback_query(FilterCallback.filter(F.action == WizardAction.CITY_DONE_SKIP))
async def on_city_done_skip(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FilterWizard.experience)
    data = await state.get_data()
    exp = data.get("experience", None)
    await _safe_edit(callback.message, text="Выбери требуемый опыт работы",
        reply_markup=build_experience_keyboard(exp),
    )
    await callback.answer()


@router.callback_query(FilterCallback.filter(F.action == WizardAction.EXPERIENCE_SELECT))
async def on_experience_select(callback: CallbackQuery, state: FSMContext):
    value = FilterCallback.unpack(callback.data).value
    if value == "__done__":
        await on_experience_done(callback, state)
        return
    if value == "__back__":
        data = await state.get_data()
        city = data.get("city", None)
        await state.set_state(FilterWizard.city)
        await _safe_edit(callback.message, text=    "Выбери город",
            reply_markup=build_city_keyboard(city),
        )
        await callback.answer()
        return
    await state.update_data(experience=value)
    await _safe_edit(callback.message, reply_markup=build_experience_keyboard(value)
    )
    await callback.answer()


async def on_experience_done(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FilterWizard.salary)
    data = await state.get_data()
    salary_key = data.get("salary_key", None)
    await _safe_edit(callback.message, text="Выбери зарплату",
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
        exp = data.get("experience", None)
        await state.set_state(FilterWizard.experience)
        await _safe_edit(callback.message, text=    "Выбери требуемый опыт работы",
            reply_markup=build_experience_keyboard(exp),
        )
        await callback.answer()
        return
    if value == "custom":
        await state.set_state(FilterWizard.custom_salary)
        await _safe_edit(callback.message, text=    "Введи желаемую зарплату цифрой (например: 250000)\n"
            "Или диапазон через дефис (например: 200000-350000)\n\n"
            "Напиши «отмена» чтобы вернуться назад.",
        )
        await callback.answer()
        return
    for key, _, smin, smax in SALARIES:
        if key == value:
            await state.update_data(salary_key=value, salary_min=smin, salary_max=smax)
            break
    await _safe_edit(callback.message, reply_markup=build_salary_keyboard(value)
    )
    await callback.answer()


@router.message(FilterWizard.custom_salary)
async def on_custom_salary(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, введи число (например: 250000)")
        return
    if message.text.strip().lower() == "отмена":
        data = await state.get_data()
        salary_key = data.get("salary_key", None)
        await state.set_state(FilterWizard.salary)
        await message.answer("Выбери зарплату",
            reply_markup=build_salary_keyboard(salary_key),
        )
        return
    text = message.text.strip().replace(" ", "").replace(",", ".")
    import re
    nums = re.findall(r"\d+", text)
    if not nums:
        await message.answer("Пожалуйста, введи число (например: 250000)")
        return
    if len(nums) == 1:
        salary_min = int(nums[0])
        salary_max = None
    else:
        salary_min = min(int(nums[0]), int(nums[1]))
        salary_max = max(int(nums[0]), int(nums[1]))

    await state.update_data(salary_key="custom", salary_min=salary_min, salary_max=salary_max)
    await state.set_state(FilterWizard.employment)

    data = await state.get_data()
    emp_types = data.get("employment_types", [])
    await message.answer(
        "Выбери тип занятости\n\n"
        "Можно выбрать несколько вариантов.",
        reply_markup=build_employment_keyboard(emp_types),
    )


async def on_salary_done(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FilterWizard.employment)
    data = await state.get_data()
    emp_types = data.get("employment_types", [])
    await _safe_edit(callback.message, text="Выбери тип занятости\n\n"
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
    await _safe_edit(callback.message, reply_markup=build_employment_keyboard(emp_types)
    )
    await callback.answer()


@router.callback_query(FilterCallback.filter(F.action == WizardAction.EMPLOYMENT_DONE))
async def on_employment_done(callback: CallbackQuery, state: FSMContext):
    value = FilterCallback.unpack(callback.data).value
    if value == "__back__":
        data = await state.get_data()
        salary_key = data.get("salary_key", None)
        await state.set_state(FilterWizard.salary)
        await _safe_edit(callback.message, text=    "Выбери зарплату",
            reply_markup=build_salary_keyboard(salary_key),
        )
        await callback.answer()
        return

    await state.set_state(FilterWizard.sites)
    data = await state.get_data()
    sites = data.get("sites", [])
    await _safe_edit(callback.message, text="Выбери сайты для поиска\n\n"
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
    await _safe_edit(callback.message, reply_markup=build_sites_keyboard(sites)
    )
    await callback.answer()


@router.callback_query(FilterCallback.filter(F.action == WizardAction.SITE_DONE))
async def on_site_done(callback: CallbackQuery, state: FSMContext):
    value = FilterCallback.unpack(callback.data).value
    if value == "__back__":
        data = await state.get_data()
        emp_types = data.get("employment_types", [])
        await state.set_state(FilterWizard.employment)
        await _safe_edit(callback.message, text=    "Выбери тип занятости",
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

    lines = [f"📋 <b>Имя:</b> {_h(name)}"]
    lines.append(f"<b>Ключевые слова:</b> {', '.join(_h(k) for k in kws)}")
    excluded = data.get("excluded_keywords", [])
    if excluded:
        lines.append(f"<b>Исключить:</b> {', '.join(_h(k) for k in excluded)}")
    city = data.get("city")
    lines.append(f"<b>Город:</b> {_h(city or 'Любой')}")
    if data.get("salary_min") is not None or data.get("salary_max") is not None:
        parts = []
        if data.get("salary_min"):
            parts.append(f"от {data['salary_min']:,}".replace(",", " "))
        if data.get("salary_max"):
            parts.append(f"до {data['salary_max']:,}".replace(",", " "))
        lines.append(f"<b>Зарплата:</b> {' '.join(parts)} ₽")
    else:
        lines.append("<b>Зарплата:</b> Любая")
    exp = data.get("experience")
    if exp:
        lines.append(f"<b>Опыт:</b> {_h(EXPERIENCE.get(exp, exp))}")
    emp_labels = [_h(EMPLOYMENT_TYPES.get(e, e)) for e in data.get("employment_types", [])]
    lines.append(f"<b>Тип занятости:</b> {', '.join(emp_labels) or 'Любой'}")
    site_labels = [_h(SITES.get(s, s)) for s in sites]
    lines.append(f"<b>Сайты:</b> {', '.join(site_labels)}")

    await _safe_edit(callback.message, text="\n".join(lines) + "\n\nСоздать этот фильтр?",
        reply_markup=build_confirm_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(FilterCallback.filter(F.action == WizardAction.CONFIRM))
async def on_confirm(callback: CallbackQuery, state: FSMContext, db: Database):
    data = await state.get_data()
    user = await db.get_or_create_user(callback.from_user.id)
    kws = list(dict.fromkeys(data["selected_keywords"]))
    exc = list(dict.fromkeys(data.get("excluded_keywords", [])))
    vf = await db.create_filter(
        user_id=user.id,
        name=data["filter_name"],
        keywords=kws,
        city=data["city"],
        salary_min=data["salary_min"],
        salary_max=data["salary_max"],
        employment_types=data["employment_types"],
        sites=data["sites"],
        exclude_keywords=exc,
        experience=data.get("experience"),
    )
    await state.clear()
    await _safe_edit(callback.message, text=f"✅ Фильтр «{_h(vf.name)}» создан!\n\n"
        f"Теперь я буду присылать подходящие вакансии раз в час.",
        reply_markup=build_start_keyboard(),
    )
    await callback.answer()
