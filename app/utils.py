"""Вспомогательные функции для базы данных, логирования и фильтрации новостей."""

import hashlib
from collections.abc import AsyncGenerator

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.news_parser.types import ParsedNewsItem


logger.add(
    "logs/aibot.log",
    rotation="10 MB",
    retention="7 days",
    level=settings.log_level,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name} | {message}",
    encoding="utf-8",
)

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
)


AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession]:
    """Возвращает асинхронную сессию базы данных для FastAPI-зависимостей."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """Создаёт таблицы базы данных, если они ещё не существуют."""
    from app.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database tables created or already exist")


def make_content_hash(title: str, url: str = "") -> str:
    """Создаёт MD5-хэш по заголовку и ссылке новости."""
    raw = f"{title.lower().strip()}|{url.lower().strip()}"
    return hashlib.md5(raw.encode()).hexdigest()


def matches_keywords(news_item: ParsedNewsItem, keywords: list[str]) -> bool:
    """Проверяет, содержит ли новость хотя бы одно активное ключевое слово."""
    if not keywords:
        return True

    text = " ".join(
        [
            news_item.get("title") or "",
            news_item.get("summary") or "",
            news_item.get("raw_text") or "",
        ]
    ).lower()

    return any(keyword.lower() in text for keyword in keywords)