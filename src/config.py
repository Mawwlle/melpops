"""Настройки приложения из переменных окружения (pydantic-settings)."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Состояние приложения, собираемое из env / .env.

    Каждое поле можно переопределить переменной окружения
    того же имени: `LOG_LEVEL=debug uv run uvicorn src.app:app`.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "melpops"
    version: str = "0.1.0"
    log_level: str = "INFO"
    debug: bool = False
    environment: str = "development"
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/melpops",
        description="Строка подключения к Postgres (asyncpg-формат).",
    )


def get_settings() -> Settings:
    """Вернуть настройки приложения."""
    return Settings()
