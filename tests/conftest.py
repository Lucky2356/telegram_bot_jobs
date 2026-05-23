import asyncio
import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator

from core.database.repository import Database
from core.database.models import Base


TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

# Disable auth middleware for tests (env var overrides .env file)
os.environ["WEB_PASSWORD"] = ""


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[Database, None]:
    database = Database(TEST_DB_URL)
    await database.create_tables()
    yield database
    await database.engine.dispose()


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
