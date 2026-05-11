"""Точка входа FastAPI-приложения."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from loguru import logger

from app.api.endpoints import router as api_router
from app.config import settings
from app.utils import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Инициализирует приложение при старте и логирует остановку сервера."""
    logger.info("AIBot starting up...")
    await init_db()
    logger.info("AIBot is ready!")

    yield

    logger.info("AIBot shutting down...")


app = FastAPI(
    title="AIBot — AI Telegram News Publisher",
    description="""
    Сервис для автоматической генерации и публикации
    AI-постов в Telegram на основе новостей.
    """,
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan,
)


@app.get("/", tags=["Health"])
async def root() -> dict[str, str]:
    """Возвращает краткую информацию о состоянии сервиса."""
    return {
        "service": "AIBot",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Возвращает статус доступности сервиса."""
    return {"status": "healthy"}


app.include_router(api_router, prefix="/api")