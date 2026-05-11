"""Парсер RSS- и Atom-лент новостных сайтов."""

from datetime import datetime
from typing import Any

import feedparser

from app.news_parser.types import ParsedNewsItem


def _parse_datetime(entry: Any) -> datetime:
    """Возвращает дату публикации RSS-записи или текущее время."""
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:6])

    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        return datetime(*entry.updated_parsed[:6])

    return datetime.utcnow()


async def parse_rss(url: str) -> list[ParsedNewsItem]:
    """Парсит RSS/Atom-ленту и возвращает список найденных новостей."""
    feed = feedparser.parse(url)

    news_items: list[ParsedNewsItem] = []

    for entry in feed.entries:
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()
        summary = entry.get("summary", "").strip()

        if not title:
            continue

        news_items.append(
            {
                "title": title,
                "url": link or None,
                "summary": summary or title,
                "source": feed.feed.get("title", url),
                "published_at": _parse_datetime(entry),
                "raw_text": summary or title,
            }
        )

    return news_items