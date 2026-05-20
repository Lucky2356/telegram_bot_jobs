import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from bot.keyboards import (
    FilterCallback, WizardAction,
    build_filters_list_keyboard, build_start_keyboard,
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
    status = "активен 🟢" if active else "на паузе 🔴"
    await callback.answer(f"Фильтр {status}")
    await callback.answer()


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
