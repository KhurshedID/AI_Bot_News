"""Настройки приложения, загружаемые из переменных окружения."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Конфигурация приложения."""

    database_url: str = "sqlite+aiosqlite:///./aibot.db"
    redis_url: str = "redis://localhost:6379/0"
    bot_token: str = ""
    tg_channel: str = ""
    chatgpt_api_key: str = ""
    debug: bool = False
    log_level: str = "INFO"

    class Config:
        """Настройки загрузки переменных окружения."""

        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    """Возвращает кэшированный объект настроек приложения."""
    return Settings()


settings = get_settings()