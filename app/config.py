"""Настройки проекта."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Класс настроек."""
    # База данных
    database_url: str = "sqlite+aiosqlite:///./aibot.db"

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"

    # Telegram Bot
    bot_token: str = ""
    tg_channel: str = ""

    # ChatGPT
    chatgpt_api_key: str = ""

    # Приложение
    debug: bool = False
    log_level: str = "INFO"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
