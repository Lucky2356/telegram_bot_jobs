from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from bot.keyboards import build_start_keyboard, FilterCallback, WizardAction, build_keywords_keyboard, build_keyword_groups_keyboard
from bot.handlers.filters import FilterWizard
from core.database.repository import Database

router = Router()


async def _safe_edit(msg, text=None, reply_markup=None):
    try:
        if text is not None:
            await msg.edit_text(text=text, reply_markup=reply_markup)
        elif reply_markup is not None:
            await msg.edit_reply_markup(reply_markup=reply_markup)
    except TelegramBadRequest as e:
        if 'message is not modified' in str(e):
            pass
        else:
            raise


@router.message(CommandStart())
async def cmd_start(message: Message, db: Database):
    await db.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
    )
    await message.answer(
        "👋 Привет! Я бот для поиска вакансий.\n\n"
        "С помощью меня ты сможешь:\n"
        "🔍 Находить вакансии с hh.ru, SuperJob, rabota.ru, "
        "Хабр Карьеры и Работы России\n"
        "⚡ Получать их в Telegram по заданным фильтрам\n"
        "🌐 Управлять фильтрами через веб-интерфейс\n\n"
        "Нажми «➕ Добавить фильтр», чтобы начать!",
        reply_markup=build_start_keyboard(),
    )


@router.callback_query(FilterCallback.filter(F.action == WizardAction.MAIN_FILTERS))
async def main_filters(callback: CallbackQuery, db: Database):
    user = await db.get_or_create_user(callback.from_user.id)
    filters = await db.get_user_filters(user.id)
    if not filters:
        await _safe_edit(callback.message, text="У тебя пока нет фильтров. Создай первый!",
            reply_markup=build_start_keyboard(),
        )
    else:
        from bot.keyboards import build_filters_list_keyboard
        await _safe_edit(callback.message, text="📋 Твои фильтры вакансий:",
            reply_markup=build_filters_list_keyboard(filters),
        )
    await callback.answer()


@router.callback_query(FilterCallback.filter(F.action == WizardAction.MAIN_ADD))
async def main_add(callback: CallbackQuery, state: FSMContext):
    await state.update_data(
        selected_keywords=[],
        excluded_keywords=[],
        experience=None,
        city=None,
        salary_key=None,
        salary_min=None,
        salary_max=None,
        employment_types=[],
        sites=[],
    )
    await state.set_state(FilterWizard.keywords)
    await _safe_edit(callback.message, text="Шаг 1 — Выбери категорию ключевых слов\n\n"
        "Нажми на категорию, чтобы увидеть слова внутри.\n"
        "Можно выбрать слова из нескольких категорий.",
        reply_markup=build_keyword_groups_keyboard([]),
    )
    await callback.answer()
