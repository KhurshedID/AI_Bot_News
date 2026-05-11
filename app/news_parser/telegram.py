"""Парсер публичных Telegram-каналов через веб-страницу t.me/s."""

from datetime import datetime
from typing import Any

import httpx
from bs4 import BeautifulSoup

from app.news_parser.types import ParsedNewsItem


def _build_tg_url(username: str) -> str:
    """Преобразует username или ссылку Telegram-канала в URL веб-версии."""
    username = username.strip()

    if username.startswith("https://t.me/s/"):
        return username

    if username.startswith("https://t.me/"):
        username = username.replace("https://t.me/", "", 1)

    if username.startswith("@"):
        username = username[1:]

    return f"https://t.me/s/{username}"


def _parse_message_datetime(message: Any) -> datetime:
    """Возвращает дату Telegram-сообщения из HTML или текущее время."""
    time_tag = message.select_one("time")

    if not time_tag:
        return datetime.utcnow()

    datetime_value = time_tag.get("datetime")

    if not datetime_value:
        return datetime.utcnow()

    try:
        return datetime.fromisoformat(datetime_value.replace("Z", "+00:00")).replace(
            tzinfo=None
        )
    except ValueError:
        return datetime.utcnow()


async def parse_tg_channel(username: str) -> list[ParsedNewsItem]:
    """Парсит публичный Telegram-канал и возвращает список сообщений."""
    url = _build_tg_url(username)

    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    messages = soup.select(".tgme_widget_message")
    news_items: list[ParsedNewsItem] = []

    for message in messages:
        text_tag = message.select_one(".tgme_widget_message_text")
        link_tag = message.select_one(".tgme_widget_message_date a")

        if not text_tag:
            continue

        text = text_tag.get_text(separator="\n", strip=True)

        if not text:
            continue

        message_url = link_tag.get("href") if link_tag else None
        title = text.split("\n", 1)[0]

        if len(title) > 150:
            title = title[:150].rstrip() + "..."

        news_items.append(
            {
                "title": title,
                "url": message_url,
                "summary": text,
                "source": username,
                "published_at": _parse_message_datetime(message),
                "raw_text": text,
            }
        )

    return news_items