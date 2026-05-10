from aiogram import Bot
from loguru import logger

from app.config import settings


async def publish_post(text: str) -> bool:
    """
    Публикует текстовый пост в Telegram-канал через Bot API.

    Для работы нужны переменные окружения:
    BOT_TOKEN — токен бота от @BotFather
    TG_CHANNEL — username канала, например @my_channel
    """
    if not settings.bot_token:
        logger.error("BOT_TOKEN is not set")
        raise ValueError("BOT_TOKEN is not set")

    if not settings.tg_channel:
        logger.error("TG_CHANNEL is not set")
        raise ValueError("TG_CHANNEL is not set")

    bot = Bot(token=settings.bot_token)

    try:
        await bot.send_message(
            chat_id=settings.tg_channel,
            text=text,
            disable_web_page_preview=False,
        )
        logger.info(f"Post published to Telegram channel: {settings.tg_channel}")
        return True

    except Exception as error:
        logger.exception(f"Telegram publishing failed: {error}")
        raise

    finally:
        await bot.session.close()