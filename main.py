import asyncio
import sys
import os
import logging
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from core.config import settings
from core.database.repository import Database
from core.scheduler import Scheduler
from bot.dispatcher import setup_dispatcher
from web.app import run_web

# Clear proxy env vars — they interfere with aiogram and httpx
for var in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
    os.environ.pop(var, None)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print("=== Job Bot Starting ===", flush=True)
    db = Database(settings.DATABASE_URL)
    try:
        from alembic.config import Config
        from alembic import command
        alembic_cfg = Config("alembic.ini")
        SQLITE_PREFIX = "sqlite+aiosqlite://"
        if settings.DATABASE_URL.startswith(SQLITE_PREFIX):
            sync_url = "sqlite+pysqlite://" + settings.DATABASE_URL[len(SQLITE_PREFIX):]
        else:
            sync_url = settings.DATABASE_URL
        alembic_cfg.set_main_option("sqlalchemy.url", sync_url)
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations applied")
    except Exception as e:
        logger.warning("Alembic migration failed (%s), using create_tables fallback", e)
        await db.create_tables()
        logger.info("Database initialized via create_tables")

    bot = Bot(
        token=settings.BOT_TOKEN,
        session=AiohttpSession(proxy=settings.TELEGRAM_PROXY or None),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    if settings.TELEGRAM_PROXY:
        logger.info("Telegram proxy is configured")
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
    aps.add_job(
        scheduler_obj.cleanup,
        "cron",
        hour=3,
        minute=0,
        id="db_cleanup",
        replace_existing=True,
    )
    aps.start()
    logger.info("Scheduler started (every %d hours)", settings.CHECK_INTERVAL_HOURS)
    logger.info("DB cleanup scheduled daily at 03:00")

    logger.info("Starting Telegram bot polling...")
    try:
        await asyncio.gather(
            dp.start_polling(bot),
            run_web(db, scheduler_obj),
            return_exceptions=True,
        )
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    finally:
        logger.info("Shutting down...")
        aps.shutdown(wait=False)
        await scheduler_obj.close()
        try:
            await bot.session.close()
        except Exception:
            pass
        try:
            await db.engine.dispose()
        except Exception:
            pass
        logger.info("Bye!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
