"""Celery-задачи для парсинга новостей, генерации и публикации постов."""

import asyncio
from datetime import datetime

from loguru import logger
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.generator import generate_post
from app.models import Keyword, NewsItem, Post, PostStatus, Source, SourceType
from app.news_parser.sites import parse_rss
from app.news_parser.telegram import parse_tg_channel
from app.news_parser.types import ParsedNewsItem
from app.telegram.publisher import publish_post
from app.utils import AsyncSessionLocal, matches_keywords
from celery_worker import celery_app


async def _get_enabled_sources(db: AsyncSession) -> list[Source]:
    """Возвращает список активных источников новостей."""
    result = await db.execute(select(Source).where(Source.enabled.is_(True)))
    return list(result.scalars().all())


async def _get_enabled_keywords(db: AsyncSession) -> list[str]:
    """Возвращает список активных ключевых слов."""
    result = await db.execute(select(Keyword).where(Keyword.enabled.is_(True)))
    return [keyword.word for keyword in result.scalars().all()]


async def _parse_source(source: Source) -> list[ParsedNewsItem]:
    """Парсит один источник новостей в зависимости от его типа."""
    if source.type == SourceType.site:
        return await parse_rss(source.url)

    if source.type == SourceType.telegram:
        return await parse_tg_channel(source.url)

    logger.warning("Unknown source type: %s", source.type)
    return []


def _build_duplicate_query(item: ParsedNewsItem) -> Select[tuple[NewsItem]]:
    """Создаёт запрос для проверки дубля новости."""
    if item.get("url"):
        return select(NewsItem).where(NewsItem.url == item["url"])

    return select(NewsItem).where(NewsItem.title == item["title"])


async def _news_exists(db: AsyncSession, item: ParsedNewsItem) -> bool:
    """Проверяет, есть ли такая новость в базе данных."""
    result = await db.execute(_build_duplicate_query(item))
    return result.scalar_one_or_none() is not None


def _build_news_item(item: ParsedNewsItem, source: Source) -> NewsItem:
    """Создаёт ORM-объект новости из результата парсинга."""
    return NewsItem(
        title=item["title"],
        url=item.get("url"),
        summary=item["summary"],
        raw_text=item.get("raw_text"),
        source=item["source"],
        source_id=source.id,
        published_at=item["published_at"],
    )


async def _save_source_news(
    db: AsyncSession,
    source: Source,
    keywords: list[str],
) -> dict[str, int]:
    """Парсит один источник, фильтрует новости и сохраняет новые записи."""
    news_items = await _parse_source(source)

    parsed_count = len(news_items)
    saved_count = 0
    skipped_count = 0

    for item in news_items:
        if not matches_keywords(item, keywords):
            skipped_count += 1
            continue

        if await _news_exists(db, item):
            skipped_count += 1
            continue

        db.add(_build_news_item(item, source))
        saved_count += 1

    return {
        "parsed_count": parsed_count,
        "saved_count": saved_count,
        "skipped_count": skipped_count,
    }


async def _parse_sources() -> dict[str, int]:
    """Парсит активные источники и сохраняет новые новости в базе данных."""
    async with AsyncSessionLocal() as db:
        sources = await _get_enabled_sources(db)
        keywords = await _get_enabled_keywords(db)

        result = {
            "parsed_count": 0,
            "saved_count": 0,
            "skipped_count": 0,
        }

        for source in sources:
            try:
                source_result = await _save_source_news(db, source, keywords)

                result["parsed_count"] += source_result["parsed_count"]
                result["saved_count"] += source_result["saved_count"]
                result["skipped_count"] += source_result["skipped_count"]

            except Exception as error:
                logger.exception("Failed to parse source %s: %s", source.name, error)

        await db.commit()

        return result


# ... existing code ...

async def _generate_posts() -> dict[str, int]:
    """Генерирует посты для новостей, у которых ещё нет связанного Post."""
    async with AsyncSessionLocal() as db:
        news_result = await db.execute(
            select(NewsItem).outerjoin(Post).where(Post.id.is_(None))
        )


async def _publish_posts() -> dict[str, int]:
    """Публикует сгенерированные посты, которые ещё не опубликованы."""
    async with AsyncSessionLocal() as db:
        posts_result = await db.execute(
            select(Post).where(Post.status == PostStatus.generated)
        )


@celery_app.task(name="app.tasks.parse_sources_task")
def parse_sources_task() -> dict[str, int]:
    """Запускает парсинг источников через Celery."""
    return asyncio.run(_parse_sources())


@celery_app.task(name="app.tasks.generate_posts_task")
def generate_posts_task() -> dict[str, int]:
    """Запускает генерацию постов через Celery."""
    return asyncio.run(_generate_posts())


@celery_app.task(name="app.tasks.publish_posts_task")
def publish_posts_task() -> dict[str, int]:
    """Запускает публикацию постов через Celery."""
    return asyncio.run(_publish_posts())


@celery_app.task(name="app.tasks.run_pipeline_task")
def run_pipeline_task() -> dict[str, dict[str, int]]:
    """Запускает полный пайплайн: парсинг, генерацию и публикацию."""
    parse_result = asyncio.run(_parse_sources())
    generate_result = asyncio.run(_generate_posts())
    publish_result = asyncio.run(_publish_posts())

    return {
        "parse": parse_result,
        "generate": generate_result,
        "publish": publish_result,
    }