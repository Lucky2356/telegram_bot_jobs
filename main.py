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


async def _wait_safely(coro, timeout: float, label: str):
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning("%s did not finish in %.1f seconds", label, timeout)
    except Exception as e:
        logger.warning("%s failed during shutdown: %s", label, e)


async def _cancel_tasks(tasks: list[asyncio.Task], timeout: float = 5.0):
    pending = [task for task in tasks if not task.done()]
    if not pending:
        return
    for task in pending:
        task.cancel()
    try:
        await asyncio.wait_for(asyncio.gather(*pending, return_exceptions=True), timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning("Some background tasks did not stop in %.1f seconds", timeout)


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
    shutdown_event = asyncio.Event()
    service_tasks: list[asyncio.Task] = []
    try:
        service_tasks = [
            asyncio.create_task(
                dp.start_polling(
                    bot,
                    polling_timeout=5,
                    handle_signals=False,
                    close_bot_session=False,
                ),
                name="telegram_polling",
            ),
            asyncio.create_task(
                run_web(db, scheduler_obj, shutdown_event=shutdown_event),
                name="web_server",
            ),
        ]
        done, _ = await asyncio.wait(service_tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            if task.cancelled():
                continue
            exc = task.exception()
            if exc is not None:
                raise exc
    except (asyncio.CancelledError, KeyboardInterrupt):
        logger.info("Stop signal received")
    finally:
        logger.info("Shutting down...")
        shutdown_event.set()
        try:
            aps.shutdown(wait=False)
        except Exception as e:
            logger.warning("APScheduler shutdown failed: %s", e)
        await _wait_safely(dp.stop_polling(), 3.0, "Telegram polling stop")
        await _cancel_tasks(service_tasks)
        await _wait_safely(scheduler_obj.close(), 5.0, "Scrapers shutdown")
        await _wait_safely(bot.session.close(), 5.0, "Telegram session close")
        await _wait_safely(db.engine.dispose(), 5.0, "Database engine dispose")
        logger.info("Bye!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
