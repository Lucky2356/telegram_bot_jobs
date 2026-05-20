from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    BOT_TOKEN: str
    SUPERJOB_API_KEY: str = ""
    DATABASE_URL: str = "sqlite+aiosqlite:///./vacancies.db"
    WEB_HOST: str = "127.0.0.1"
    WEB_PORT: int = 8000
    CHECK_INTERVAL_HOURS: int = 1


settings = Settings()
