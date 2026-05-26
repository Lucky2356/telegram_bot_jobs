import os
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_PATH = os.path.join(os.path.dirname(__file__), "..", ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_PATH, env_file_encoding="utf-8")

    BOT_TOKEN: str
    SUPERJOB_API_KEY: str = ""
    HH_CLIENT_ID: str = ""
    HH_CLIENT_SECRET: str = ""
    HH_USER_AGENT: str = "TelegramJobBot/1.0 (job-bot)"
    DATABASE_URL: str = "sqlite+aiosqlite:///./vacancies.db"
    WEB_HOST: str = "127.0.0.1"
    WEB_PORT: int = 8000
    WEB_CORS_ORIGINS: str = "http://127.0.0.1:8000,http://localhost:8000"
    WEB_RATE_LIMIT_WINDOW_SECONDS: int = 60
    WEB_LOGIN_RATE_LIMIT: int = 10
    WEB_ACTION_RATE_LIMIT: int = 20
    WEB_SESSION_TTL_SECONDS: int = 86400
    WEB_PASSWORD_HASH: str = ""
    WEB_PARSER_HEALTH_CACHE_SECONDS: int = 300
    BACKUP_DIR: str = "backups"
    SEARCH_CACHE_SECONDS: int = 600
    SEARCH_MAX_QUERIES: int = 12
    SEARCH_SITE_CONCURRENCY: int = 2
    LOG_MAX_BYTES: int = 5_000_000
    LOG_BACKUP_COUNT: int = 5
    CHECK_INTERVAL_HOURS: int = 1
    WEB_PASSWORD: str = ""
    JWT_SECRET: str = ""
    TELEGRAM_PROXY: str = ""


settings = Settings()
