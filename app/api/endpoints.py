from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.generator import generate_post
from app.telegram.publisher import publish_post

from app.api.schemas import (
    GenerateRequest,
    GenerateResponse,
    KeywordCreate,
    KeywordRead,
    KeywordUpdate,
    NewsItemRead,
    ParseRssRequest,
    ParseSaveResponse,
    ParseTelegramRequest,
    ParsedNewsItem,
    PostRead,
    SourceCreate,
    SourceRead,
    SourceUpdate,
    TaskResponse,
)
from app.models import Keyword, NewsItem, Post, PostStatus, Source
from app.utils import get_db, matches_keywords
from app.tasks import run_pipeline_task
from app.news_parser.sites import parse_rss
from app.news_parser.telegram import parse_tg_channel

router = APIRouter(tags=["Sources"])

@router.get("/sources", response_model=list[SourceRead], tags=["Sources"])
async def list_sources(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Source).order_by(Source.created_at.desc()))
    return result.scalars().all()

@router.get("/sources/{source_id}", response_model=SourceRead, tags=["Sources"])
async def get_source(
    source_id: str,
    db: AsyncSession = Depends(get_db),
):
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source

@router.post("/sources", response_model=SourceRead, status_code=status.HTTP_201_CREATED, tags=["Sources"],)
async def create_source(
    payload: SourceCreate,
    db: AsyncSession = Depends(get_db),
):
    source = Source(**payload.model_dump())
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return source

@router.patch("/sources/{source_id}", response_model=SourceRead, tags=["Sources"])
async def update_source(
    source_id: str,
    payload: SourceUpdate,
    db: AsyncSession = Depends(get_db),
):
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(source, field, value)

    await db.commit()
    await db.refresh(source)
    return source

@router.delete(
    "/sources/{source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Sources"],
)
async def delete_source(
    source_id: str,
    db: AsyncSession = Depends(get_db),
):
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    await db.delete(source)
    await db.commit()
    return None


@router.get("/keywords", response_model=list[KeywordRead], tags=["Keywords"])
async def list_keywords(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Keyword).order_by(Keyword.created_at.desc()))
    return result.scalars().all()


@router.get("/keywords/{keyword_id}", response_model=KeywordRead, tags=["Keywords"])
async def get_keyword(
    keyword_id: str,
    db: AsyncSession = Depends(get_db),
):
    keyword = await db.get(Keyword, keyword_id)
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    return keyword


@router.post(
    "/keywords",
    response_model=KeywordRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Keywords"],
)
async def create_keyword(
    payload: KeywordCreate,
    db: AsyncSession = Depends(get_db),
):
    keyword = Keyword(**payload.model_dump())
    db.add(keyword)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Keyword already exists or invalid data",
        )
    await db.refresh(keyword)
    return keyword


@router.patch("/keywords/{keyword_id}", response_model=KeywordRead, tags=["Keywords"])
async def update_keyword(
    keyword_id: str,
    payload: KeywordUpdate,
    db: AsyncSession = Depends(get_db),
):
    keyword = await db.get(Keyword, keyword_id)
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(keyword, field, value)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Keyword already exists or invalid data",
        )

    await db.refresh(keyword)
    return keyword


@router.delete(
    "/keywords/{keyword_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Keywords"],
)
async def delete_keyword(
    keyword_id: str,
    db: AsyncSession = Depends(get_db),
):
    keyword = await db.get(Keyword,keyword_id)
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")

    await db.delete(keyword)
    await db.commit()
    return None


@router.get("/news", response_model=list[NewsItemRead], tags=["News"])
async def list_news(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(NewsItem).order_by(NewsItem.created_at.desc()))
    return result.scalars().all()


@router.get("/news/{news_id}", response_model=NewsItemRead, tags=["News"])
async def get_news_item(
    news_id: str,
    db: AsyncSession = Depends(get_db),
):
    news_item = await db.get(NewsItem, news_id)
    if not news_item:
        raise HTTPException(status_code=404, detail="News item not found")
    return news_item


@router.get("/posts", response_model=list[PostRead], tags=["Posts"])
async def list_posts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Post).order_by(Post.created_at.desc()))
    return result.scalars().all()


@router.get("/posts/{post_id}", response_model=PostRead, tags=["Posts"])
async def get_post(
        post_id: str,
        db: AsyncSession = Depends(get_db),
):
    post = await db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.post("/news/{news_id}/generate", response_model=PostRead, tags=["AI"])
async def generate_post_from_news(
    news_id: str,
    db: AsyncSession = Depends(get_db),
):
    news_item = await db.get(NewsItem, news_id)

    if not news_item:
        raise HTTPException(status_code=404, detail="News item not found")

    existing_post_result = await db.execute(
        select(Post).where(Post.news_id == news_id)
    )
    existing_post = existing_post_result.scalar_one_or_none()

    if existing_post:
        return existing_post

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
    await db.commit()
    await db.refresh(post)

    return post


@router.post("/posts/{post_id}/publish", response_model=PostRead, tags=["Telegram"])
async def publish_generated_post(
    post_id: str,
    db: AsyncSession = Depends(get_db),
):
    post = await db.get(Post, post_id)

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.status == PostStatus.published:
        return post

    try:
        await publish_post(post.generated_text)

        post.status = PostStatus.published
        post.published_at = datetime.utcnow()
        post.error_message = None

        await db.commit()
        await db.refresh(post)

        return post

    except Exception as error:
        post.status = PostStatus.failed
        post.error_message = str(error)

        await db.commit()
        await db.refresh(post)

        raise HTTPException(
            status_code=500,
            detail=f"Telegram publishing failed: {error}",
        )


@router.post("/generate", response_model=GenerateResponse, tags=["AI"])
async def generate_manually(payload: GenerateRequest):
    generated_text = await generate_post(payload.text)
    return GenerateResponse(generated_text=generated_text)


@router.post("/parse/rss", response_model=list[ParsedNewsItem], tags=["Parsers"])
async def parse_rss_manually(payload: ParseRssRequest):
    news_items = await parse_rss(payload.url)
    return news_items[:10]


@router.post("/parse/rss/save", response_model=ParseSaveResponse, tags=["Parsers"])
async def parse_rss_and_save(
    payload: ParseRssRequest,
    db: AsyncSession = Depends(get_db),
):
    news_items = await parse_rss(payload.url)

    keywords_result = await db.execute(
        select(Keyword).where(Keyword.enabled.is_(True))
    )
    keywords = [keyword.word for keyword in keywords_result.scalars().all()]

    saved_count = 0
    skipped_count = 0
    filtered_count = 0

    for item in news_items:
        if not matches_keywords(item, keywords):
            filtered_count += 1
            continue

        if item.get("url"):
            existing_query = select(NewsItem).where(NewsItem.url == item["url"])
        else:
            existing_query = select(NewsItem).where(NewsItem.title == item["title"])

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
            published_at=item["published_at"],
        )

        db.add(news_item)
        saved_count += 1

    await db.commit()

    return ParseSaveResponse(
        parsed_count=len(news_items),
        saved_count=saved_count,
        skipped_count=skipped_count + filtered_count,
    )


@router.post("/parse/telegram", response_model=list[ParsedNewsItem], tags=["Parsers"])
async def parse_telegram_manually(payload: ParseTelegramRequest):
    news_items = await parse_tg_channel(payload.username)
    return news_items[:10]


@router.post("/tasks/run-pipeline", response_model=TaskResponse, tags=["Tasks"])
async def run_pipeline():
    task = run_pipeline_task.delay()

    return TaskResponse(
        task_id=task.id,
        status="queued",
    )