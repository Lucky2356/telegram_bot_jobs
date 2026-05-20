import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from bot.keyboards import (
    FilterCallback, WizardAction,
    build_filters_list_keyboard, build_start_keyboard,
    build_filter_detail_keyboard, EMPLOYMENT_TYPES, SITES, SALARIES, EXPERIENCE,
)
from core.database.repository import Database
from core.scheduler import Scheduler

router = Router()


@router.message(Command("filters"))
async def cmd_filters(message: Message, db: Database):
    user = await db.get_or_create_user(message.from_user.id)
    filters = await db.get_user_filters(user.id)
    if not filters:
        await message.answer(
            "У тебя пока нет фильтров. Создай первый через /start!",
        )
        return
    await message.answer(
        "📋 Твои фильтры:",
        reply_markup=build_filters_list_keyboard(filters),
    )


@router.callback_query(FilterCallback.filter(F.action == WizardAction.FILTER_TOGGLE))
async def on_filter_toggle(callback: CallbackQuery, db: Database):
    filter_id = int(FilterCallback.unpack(callback.data).value)
    active = await db.toggle_filter(filter_id)
    user = await db.get_or_create_user(callback.from_user.id)
    filters = await db.get_user_filters(user.id)
    await callback.message.edit_reply_markup(
        reply_markup=build_filters_list_keyboard(filters)
    )
    status = "🟢 активен" if active else "🔴 на паузе"
    await callback.answer(f"Фильтр {status}")


@router.callback_query(FilterCallback.filter(F.action == WizardAction.FILTER_DELETE))
async def on_filter_delete(callback: CallbackQuery, db: Database):
    filter_id = int(FilterCallback.unpack(callback.data).value)
    await db.delete_filter(filter_id)
    user = await db.get_or_create_user(callback.from_user.id)
    filters = await db.get_user_filters(user.id)
    if filters:
        await callback.message.edit_reply_markup(
            reply_markup=build_filters_list_keyboard(filters)
        )
    else:
        await callback.message.edit_text(
            "Фильтр удалён. У тебя больше нет фильтров.",
            reply_markup=build_start_keyboard(),
        )
    await callback.answer("Фильтр удалён 🗑")


@router.callback_query(FilterCallback.filter(F.action == WizardAction.FILTER_VIEW))
async def on_filter_view(callback: CallbackQuery, db: Database):
    filter_id = int(FilterCallback.unpack(callback.data).value)
    vf = await db.get_filter(filter_id)
    if vf is None:
        await callback.answer("Фильтр не найден", show_alert=True)
        return
    lines = [f"📋 <b>{vf.name}</b>"]
    lines.append(f"<b>Статус:</b> {'🟢 Активен' if vf.active else '🔴 На паузе'}")
    lines.append(f"<b>Ключевые слова:</b> {', '.join(vf.get_keywords())}")
    exc = vf.get_exclude_keywords()
    if exc:
        lines.append(f"<b>Исключить:</b> {', '.join(exc)}")
    lines.append(f"<b>Город:</b> {vf.city or 'Любой'}")
    if vf.salary_min is not None or vf.salary_max is not None:
        parts = []
        if vf.salary_min is not None:
            parts.append(f"от {vf.salary_min:,}".replace(",", " "))
        if vf.salary_max is not None:
            parts.append(f"до {vf.salary_max:,}".replace(",", " "))
        lines.append(f"<b>Зарплата:</b> {' '.join(parts)} ₽")
    else:
        lines.append("<b>Зарплата:</b> Любая")
    emp_labels = [EMPLOYMENT_TYPES.get(e, e) for e in vf.get_employment_types()]
    lines.append(f"<b>Занятость:</b> {', '.join(emp_labels) or 'Любая'}")
    if vf.experience:
        lines.append(f"<b>Опыт:</b> {EXPERIENCE.get(vf.experience, vf.experience)}")
    site_labels = [SITES.get(s, s) for s in vf.get_sites()]
    lines.append(f"<b>Сайты:</b> {', '.join(site_labels)}")
    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=build_filter_detail_keyboard(vf.id, vf.active),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(FilterCallback.filter(F.action == WizardAction.FILTER_CLONE))
async def on_filter_clone(callback: CallbackQuery, db: Database):
    filter_id = int(FilterCallback.unpack(callback.data).value)
    vf = await db.get_filter(filter_id)
    if vf is None:
        await callback.answer("Фильтр не найден", show_alert=True)
        return
    new_vf = await db.create_filter(
        user_id=vf.user_id,
        name=vf.name + " (копия)",
        keywords=vf.get_keywords(),
        city=vf.city,
        salary_min=vf.salary_min,
        salary_max=vf.salary_max,
        employment_types=vf.get_employment_types(),
        sites=vf.get_sites(),
        exclude_keywords=vf.get_exclude_keywords(),
        experience=vf.experience,
    )
    user = await db.get_or_create_user(callback.from_user.id)
    filters = await db.get_user_filters(user.id)
    await callback.message.edit_text(
        f"✅ Фильтр «{new_vf.name}» создан из копии «{vf.name}»",
        reply_markup=build_filters_list_keyboard(filters),
    )
    await callback.answer()


@router.message(Command("pause"))
async def cmd_pause(message: Message, db: Database):
    user = await db.get_or_create_user(message.from_user.id)
    filters = await db.get_user_filters(user.id)
    count = 0
    for vf in filters:
        if vf.active:
            await db.toggle_filter(vf.id)
            count += 1
    await message.answer(f"⏸ {count} фильтров поставлено на паузу.")


@router.message(Command("stats"))
async def cmd_stats(message: Message, db: Database):
    user = await db.get_or_create_user(message.from_user.id)
    filters = await db.get_user_filters(user.id)
    active = sum(1 for vf in filters if vf.active)
    from core.database.models import Vacancy, SentVacancy
    from sqlalchemy import select, func
    async with db.session_factory() as session:
        total_vac = (await session.execute(select(func.count(Vacancy.id)))).scalar() or 0
        total_sent = (
            await session.execute(
                select(func.count(SentVacancy.id)).where(SentVacancy.user_id == user.id)
            )
        ).scalar() or 0
        site_counts = (
            await session.execute(
                select(Vacancy.source, func.count(Vacancy.id))
                .select_from(SentVacancy)
                .join(Vacancy, SentVacancy.vacancy_id == Vacancy.id)
                .where(SentVacancy.user_id == user.id)
                .group_by(Vacancy.source)
            )
        ).all()
    site_lines = "".join(f"\n• <b>{s or '?'}:</b> {c}" for s, c in site_counts)
    await message.answer(
        f"📊 <b>Статистика</b>\n\n"
        f"🔸 Фильтров: {len(filters)} (активных: {active})\n"
        f"🔸 Всего вакансий в базе: {total_vac}\n"
        f"🔸 Отправлено тебе: {total_sent}"
        + site_lines,
        parse_mode="HTML",
    )


@router.message(Command("resume"))
async def cmd_resume(message: Message, db: Database):
    user = await db.get_or_create_user(message.from_user.id)
    filters = await db.get_user_filters(user.id)
    count = 0
    for vf in filters:
        if not vf.active:
            await db.toggle_filter(vf.id)
            count += 1
    await message.answer(f"▶️ {count} фильтров возобновлено.")


@router.callback_query(FilterCallback.filter(F.action == WizardAction.CHECK_NOW))
async def on_check_now(callback: CallbackQuery, scheduler: Scheduler):
    await callback.message.edit_text("🔍 Проверяю вакансии...")
    if scheduler:
        asyncio.create_task(scheduler.run_check())
        await callback.message.answer(
            "✅ Проверка запущена!",
            reply_markup=build_start_keyboard(),
        )
    else:
        await callback.message.answer(
            "❌ Шедулер не доступен.",
            reply_markup=build_start_keyboard(),
        )
    await callback.answer()
