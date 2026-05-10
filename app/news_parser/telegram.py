from datetime import datetime

import httpx
from bs4 import BeautifulSoup


def _build_tg_url(username: str) -> str:
    """
    Приводит username или ссылку Telegram-канала к формату https://t.me/s/channel
    """
    username = username.strip()

    if username.startswith("https://t.me/s/"):
        return username

    if username.startswith("https://t.me/"):
        username = username.replace("https://t.me/", "", 1)

    if username.startswith("@"):
        username = username[1:]

    return f"https://t.me/s/{username}"


def _parse_message_datetime(message) -> datetime:
    """
    Достаёт дату сообщения из HTML Telegram.
    Если дата не найдена — ставит текущее время.
    """
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


async def parse_tg_channel(username: str) -> list[dict]:
    """
    Парсинг публичного Telegram-канала через https://t.me/s/channelname.

    Работает только с публичными каналами.
    """
    url = _build_tg_url(username)

    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    messages = soup.select(".tgme_widget_message")
    news_items = []

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