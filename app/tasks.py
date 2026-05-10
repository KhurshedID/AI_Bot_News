import asyncio
from datetime import datetime

from loguru import logger
from sqlalchemy import select

from app.ai.generator import generate_post
from app.models import Keyword, NewsItem, Post, PostStatus, Source, SourceType
from app.telegram.publisher import publish_post
from app.utils import AsyncSessionLocal, matches_keywords
from celery_worker import celery_app

from app.news_parser.sites import parse_rss
from app.news_parser.telegram import parse_tg_channel


async def _parse_sources() -> dict:
    """
    Парсит все активные RSS-источники и сохраняет новые новости в БД.
    """
    async with AsyncSessionLocal() as db:
        sources_result = await db.execute(
            select(Source).where(Source.enabled.is_(True))
        )
        sources = sources_result.scalars().all()

        keywords_result = await db.execute(
            select(Keyword).where(Keyword.enabled.is_(True))
        )
        keywords = [keyword.word for keyword in keywords_result.scalars().all()]

        parsed_count = 0
        saved_count = 0
        skipped_count = 0

        for source in sources:
            try:
                if source.type == SourceType.site:
                    news_items = await parse_rss(source.url)
                elif source.type == SourceType.telegram:
                    news_items = await parse_tg_channel(source.url)
                else:
                    logger.warning(f"Unknown source type: {source.type}")
                    continue

                parsed_count += len(news_items)

                for item in news_items:
                    if not matches_keywords(item, keywords):
                        skipped_count += 1
                        continue

                    if item.get("url"):
                        existing_query = select(NewsItem).where(
                            NewsItem.url == item["url"]
                        )
                    else:
                        existing_query = select(NewsItem).where(
                            NewsItem.title == item["title"]
                        )

                    existing_result = await db.execute(existing_query)
                    existing_news = existing_result.scalar_one_or_none()

                    if existing_news:
                        skipped_count += 1
                        continue

                    news_item = NewsItem(
                        title=item["title"],
                        url=item.get("url"),
                        summary=item["summary"],
                        raw_text=item.get("raw_text"),
                        source=item["source"],
                        source_id=source.id,
                        published_at=item["published_at"],
                    )

                    db.add(news_item)
                    saved_count += 1

            except Exception as error:
                logger.exception(f"Failed to parse source {source.name}: {error}")

        await db.commit()

        return {
            "parsed_count": parsed_count,
            "saved_count": saved_count,
            "skipped_count": skipped_count,
        }


async def _generate_posts() -> dict:
    """
    Генерирует посты для новостей, у которых ещё нет Post.
    """
    async with AsyncSessionLocal() as db:
        news_result = await db.execute(
            select(NewsItem).outerjoin(Post).where(Post.id.is_(None))
        )
        news_items = news_result.scalars().all()

        generated_count = 0
        failed_count = 0

        for news_item in news_items:
            try:
                news_text = "\n\n".join(
                    [
                        news_item.title,
                        news_item.summary,
                        news_item.raw_text or "",
                        news_item.url or "",
                    ]
                ).strip()

                generated_text = await generate_post(news_text)

                post = Post(
                    news_id=news_item.id,
                    generated_text=generated_text,
                    status=PostStatus.generated,
                )

                db.add(post)
                generated_count += 1

            except Exception as error:
                logger.exception(
                    f"Failed to generate post for news {news_item.id}: {error}"
                )
                failed_count += 1

        await db.commit()

        return {
            "generated_count": generated_count,
            "failed_count": failed_count,
        }


async def _publish_posts() -> dict:
    """
    Публикует все сгенерированные посты, которые ещё не опубликованы.
    """
    async with AsyncSessionLocal() as db:
        posts_result = await db.execute(
            select(Post).where(Post.status == PostStatus.generated)
        )
        posts = posts_result.scalars().all()

        published_count = 0
        failed_count = 0

        for post in posts:
            try:
                await publish_post(post.generated_text)

                post.status = PostStatus.published
                post.published_at = datetime.utcnow()
                post.error_message = None

                published_count += 1

            except Exception as error:
                logger.exception(f"Failed to publish post {post.id}: {error}")

                post.status = PostStatus.failed
                post.error_message = str(error)

                failed_count += 1

        await db.commit()

        return {
            "published_count": published_count,
            "failed_count": failed_count,
        }


@celery_app.task(name="app.tasks.parse_sources_task")
def parse_sources_task() -> dict:
    return asyncio.run(_parse_sources())


@celery_app.task(name="app.tasks.generate_posts_task")
def generate_posts_task() -> dict:
    return asyncio.run(_generate_posts())


@celery_app.task(name="app.tasks.publish_posts_task")
def publish_posts_task() -> dict:
    return asyncio.run(_publish_posts())


@celery_app.task(name="app.tasks.run_pipeline_task")
def run_pipeline_task() -> dict:
    parse_result = asyncio.run(_parse_sources())
    generate_result = asyncio.run(_generate_posts())
    publish_result = asyncio.run(_publish_posts())

    return {
        "parse": parse_result,
        "generate": generate_result,
        "publish": publish_result,
    }