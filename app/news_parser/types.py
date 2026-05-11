"""Типы данных для результатов парсинга новостей."""

from datetime import datetime
from typing import TypedDict


class ParsedNewsItem(TypedDict):
    """Новость, полученная из RSS-ленты или Telegram-канала."""

    title: str
    url: str | None
    summary: str
    source: str
    published_at: datetime
    raw_text: str