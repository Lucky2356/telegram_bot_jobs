from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.keyboards import (
    FilterCallback, WizardAction,
)
from bot.handlers.filters import FilterWizard
from core.database.repository import Database

router = Router()


@router.callback_query(FilterCallback.filter(F.action == WizardAction.VAC_SAVE))
async def on_vacancy_save(callback: CallbackQuery, db: Database):
    vacancy_id = int(FilterCallback.unpack(callback.data).value)
    user = await db.get_or_create_user(callback.from_user.id)
    await db.save_vacancy(user.id, vacancy_id)
    await callback.answer("✅ Вакансия сохранена!")


@router.callback_query(FilterCallback.filter(F.action == WizardAction.VAC_BLOCK))
async def on_vacancy_block(callback: CallbackQuery, db: Database):
    value = FilterCallback.unpack(callback.data).value
    parts = value.split("|", 1)
    if len(parts) != 2:
        await callback.answer("Ошибка")
        return
    vacancy_id, source = int(parts[0]), parts[1]
    user = await db.get_or_create_user(callback.from_user.id)
    from core.database.models import Vacancy
    from sqlalchemy import select
    async with db.session_factory() as session:
        result = await session.execute(select(Vacancy).where(Vacancy.id == vacancy_id))
        vac = result.scalar_one_or_none()
        if vac and vac.company:
            await db.add_blocklist(user.id, vac.company, "company")
    await callback.answer("🚫 Компания добавлена в блок-лист!")


@router.callback_query(FilterCallback.filter(F.action == WizardAction.VAC_SIMILAR))
async def on_vacancy_similar(callback: CallbackQuery, state: FSMContext, db: Database):
    vacancy_id = int(FilterCallback.unpack(callback.data).value)
    from core.database.models import Vacancy
    from sqlalchemy import select
    async with db.session_factory() as session:
        result = await session.execute(select(Vacancy).where(Vacancy.id == vacancy_id))
        vac = result.scalar_one_or_none()

    if not vac:
        await callback.answer("Вакансия не найдена", show_alert=True)
        return

    words = vac.title.replace("/", " ").replace("-", " ").split()
    keywords = [w for w in words if len(w) > 2][:5]

    await state.update_data(
        filter_name=", ".join(keywords),
        selected_keywords=keywords,
        excluded_keywords=[],
        city=None,
        salary_key=None,
        salary_min=None,
        salary_max=None,
        employment_types=[],
        sites=["hh", "superjob", "rabota", "habr", "trudvsem"],
    )
    await state.set_state(FilterWizard.confirm)

    lines = [f"📋 <b>Фильтр из вакансии:</b>"]
    lines.append(f"<b>Ключевые слова:</b> {', '.join(keywords)}")
    lines.append("<b>Город:</b> Любой")
    lines.append("<b>Зарплата:</b> Любая")
    lines.append("<b>Сайты:</b> Все")

    from bot.keyboards import build_confirm_keyboard
    from bot.handlers.filters import _safe_edit as _se
    await _se(callback.message,
        text="\n".join(lines) + "\n\nСоздать этот фильтр?",
        reply_markup=build_confirm_keyboard(),
    )
    await callback.answer()
