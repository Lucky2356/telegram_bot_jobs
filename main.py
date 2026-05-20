import asyncio
import logging
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from core.config import settings
from core.database.repository import Database
from core.scheduler import Scheduler
from bot.dispatcher import setup_dispatcher
from web.app import run_web

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def main():
    db = Database(settings.DATABASE_URL)
    await db.create_tables()
    logger.info("Database initialized")

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    scheduler_obj = Scheduler(db, bot)
    dp = setup_dispatcher(db, scheduler_obj)

    aps = AsyncIOScheduler()
    aps.add_job(
        scheduler_obj.run_check,
        "interval",
        hours=settings.CHECK_INTERVAL_HOURS,
        id="vacancy_check",
        replace_existing=True,
    )
    aps.start()
    logger.info("Scheduler started (every %d hours)", settings.CHECK_INTERVAL_HOURS)

    logger.info("Starting Telegram bot polling...")
    await asyncio.gather(
        dp.start_polling(bot),
        run_web(db, scheduler_obj),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
