# Занятие 3: генерация постов через Claude API
from openai import AsyncOpenAI
from loguru import logger

from app.config import settings


async def generate_post(news_text: str) -> str:
    """
    Генерирует короткий Telegram-пост на основе текста новости.

    Если API-ключ не указан, возвращает тестовый пост,
    чтобы проект мог работать локально без внешнего AI API.
    """
    if not settings.chatgpt_api_key:
        logger.warning("CHATGPT_API_KEY is not set. Using fallback generation.")
        return _generate_fallback_post(news_text)

    client = AsyncOpenAI(api_key=settings.chatgpt_api_key)

    prompt = (
        "Сделай краткий, интересный пост для Telegram-канала на русском языке. "
        "Добавь 1-3 emoji, сохрани смысл новости, не выдумывай факты, "
        "в конце добавь короткий call to action.\n\n"
        f"Текст новости:\n{news_text}"
    )

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты редактор новостного Telegram-канала. "
                        "Пиши кратко, понятно и интересно."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.7,
            max_tokens=500,
        )

        generated_text = response.choices[0].message.content

        if not generated_text:
            logger.warning("OpenAI returned empty response. Using fallback generation.")
            return _generate_fallback_post(news_text)

        return generated_text.strip()

    except Exception as error:
        logger.exception(f"AI generation failed: {error}")
        return _generate_fallback_post(news_text)


def _generate_fallback_post(news_text: str) -> str:
    """
    Запасная генерация без AI.

    Нужна, чтобы проект не падал, если нет API-ключа
    или OpenAI временно недоступен.
    """
    short_text = news_text.strip()

    if len(short_text) > 500:
        short_text = short_text[:500].rstrip() + "..."

    return (
        "📰 Кратко о важном!\n\n"
        f"{short_text}\n\n"
        "👉 Следите за обновлениями, чтобы не пропустить главное."
    )