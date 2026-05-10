import hashlib
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.config import settings


#логирование
logger.add(
    "logs/aibot.log",
    rotation="10 MB",      # новый файл каждые 10 МБ
    retention="7 days",    # хранить 7 дней
    level=settings.log_level,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name} | {message}",
    encoding="utf-8",
)

#бд
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,   # если DEBUG=True — печатает SQL запросы
)


AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """Dependency для FastAPI — даёт сессию БД в роут"""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """Создаём все таблицы при старте приложения"""
    from app.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created (or already exist)")


def make_content_hash(title: str, url: str = "") -> str:
    """
    MD5-хэш для дедупликации новостей.
    Две новости с одинаковым title+url → одинаковый хэш.
    """
    raw = f"{title.lower().strip()}|{url.lower().strip()}"
    return hashlib.md5(raw.encode()).hexdigest()


def matches_keywords(news_item: dict, keywords: list[str]) -> bool:
    """
    Проверяет, подходит ли новость под список ключевых слов.

    Если ключевых слов нет — новость считается подходящей.
    Если ключевые слова есть — хотя бы одно слово должно встретиться
    в title, summary или raw_text.
    """
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