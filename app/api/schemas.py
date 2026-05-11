"""Pydantic-схемы для запросов и ответов REST API."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models import PostStatus, SourceType


class SourceCreate(BaseModel):
    """Данные для создания источника новостей."""

    name: str = Field(..., max_length=255)
    type: SourceType = SourceType.site
    url: str = Field(..., max_length=512)
    enabled: bool = True


class SourceUpdate(BaseModel):
    """Данные для частичного обновления источника новостей."""

    name: str | None = Field(default=None, max_length=255)
    type: SourceType | None = None
    url: str | None = Field(default=None, max_length=512)
    enabled: bool | None = None


class SourceRead(BaseModel):
    """Данные источника новостей в API-ответе."""

    id: str
    name: str
    type: SourceType
    url: str
    enabled: bool
    created_at: datetime

    class Config:
        """Настройки чтения данных из ORM-моделей."""

        from_attributes = True


class KeywordCreate(BaseModel):
    """Данные для создания ключевого слова."""

    word: str = Field(..., max_length=255)
    enabled: bool = True


class KeywordUpdate(BaseModel):
    """Данные для частичного обновления ключевого слова."""

    word: str | None = Field(default=None, max_length=255)
    enabled: bool | None = None


class KeywordRead(BaseModel):
    """Данные ключевого слова в API-ответе."""

    id: str
    word: str
    enabled: bool
    created_at: datetime

    class Config:
        """Настройки чтения данных из ORM-моделей."""

        from_attributes = True


class NewsItemRead(BaseModel):
    """Данные новости в API-ответе."""

    id: str
    title: str
    url: str | None
    summary: str
    raw_text: str | None
    source: str
    source_id: str | None
    published_at: datetime
    created_at: datetime

    class Config:
        """Настройки чтения данных из ORM-моделей."""

        from_attributes = True


class PostRead(BaseModel):
    """Данные сгенерированного поста в API-ответе."""

    id: str
    news_id: str
    generated_text: str
    status: PostStatus
    published_at: datetime | None
    error_message: str | None
    created_at: datetime

    class Config:
        """Настройки чтения данных из ORM-моделей."""

        from_attributes = True


class GenerateRequest(BaseModel):
    """Запрос на ручную генерацию поста."""

    text: str = Field(..., min_length=10)


class GenerateResponse(BaseModel):
    """Ответ с текстом сгенерированного поста."""

    generated_text: str


class ParseRssRequest(BaseModel):
    """Запрос на ручной парсинг RSS-ленты."""

    url: str = Field(..., max_length=512)


class ParsedNewsItem(BaseModel):
    """Новость, полученная парсером."""

    title: str
    url: str | None
    summary: str
    source: str
    published_at: datetime
    raw_text: str | None


class ParseSaveResponse(BaseModel):
    """Статистика парсинга и сохранения новостей."""

    parsed_count: int
    saved_count: int
    skipped_count: int


class TaskResponse(BaseModel):
    """Ответ после постановки фоновой задачи в очередь."""

    task_id: str
    status: str


class ParseTelegramRequest(BaseModel):
    """Запрос на ручной парсинг публичного Telegram-канала."""

    username: str = Field(..., max_length=512)