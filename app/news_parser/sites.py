# Занятие 2: RSS и HTTP парсинг сайтов
# TODO: реализовать parse_rss() и parse_site()
from datetime import datetime

import feedparser


def _parse_datetime(entry) -> datetime:
    """
    Достаём дату публикации из RSS-записи.
    Если даты нет — ставим текущую дату.
    """
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:6])

    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        return datetime(*entry.updated_parsed[:6])

    return datetime.utcnow()


async def parse_rss(url: str) -> list[dict]:
    """
    Парсинг RSS/Atom-ленты.

    На вход получает URL RSS-ленты.
    На выход возвращает список словарей с новостями.
    """
    feed = feedparser.parse(url)

    news_items = []

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