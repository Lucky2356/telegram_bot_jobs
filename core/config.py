import os
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_PATH = os.path.join(os.path.dirname(__file__), "..", ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_PATH, env_file_encoding="utf-8")

    BOT_TOKEN: str
    SUPERJOB_API_KEY: str = ""
    HH_CLIENT_ID: str = ""
    HH_CLIENT_SECRET: str = ""
    DATABASE_URL: str = "sqlite+aiosqlite:///./vacancies.db"
    WEB_HOST: str = "127.0.0.1"
    WEB_PORT: int = 8000
    CHECK_INTERVAL_HOURS: int = 1
    WEB_PASSWORD: str = ""


settings = Settings()
