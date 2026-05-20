from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from core.database.repository import Database
from core.scheduler import Scheduler


def setup_dispatcher(db: Database, scheduler: Scheduler | None = None) -> Dispatcher:
    from bot.handlers.start import router as start_router
    from bot.handlers.filters import router as filters_router
    from bot.handlers.control import router as control_router

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage, db=db, scheduler=scheduler)

    dp.include_router(start_router)
    dp.include_router(filters_router)
    dp.include_router(control_router)

    return dp
