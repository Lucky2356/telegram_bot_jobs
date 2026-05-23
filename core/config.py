from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    BOT_TOKEN: str
    SUPERJOB_API_KEY: str = "v3.r.126319568.fbdb1551a60ebe53cfa7886dda42dac89cb549de.b826d3bbffa054d0797db3c2b0998845adac7704"
    HH_CLIENT_ID: str = "L3S26CNP49P4QH9CM2PM573PN493LIA2FDCLPCBMBHPQA3Q7OUEILAH666J5VC5C"
    HH_CLIENT_SECRET: str = "T3E5K2R2L0UTUTILBB4HHBTVBTBF7APBPF751ON048SVJ5UDN0BBVDDLCGVBNG0I"
    DATABASE_URL: str = "sqlite+aiosqlite:///./vacancies.db"
    WEB_HOST: str = "127.0.0.1"
    WEB_PORT: int = 8000
    CHECK_INTERVAL_HOURS: int = 1
    WEB_PASSWORD: str = "F65Hei812QF!"


settings = Settings()
