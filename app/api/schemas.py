from datetime import datetime
from pydantic import BaseModel, Field

from app.models import SourceType, PostStatus


class SourceCreate(BaseModel):
    name: str = Field(..., max_length=255)
    type: SourceType = SourceType.site
    url: str = Field(..., max_length=512)
    enabled: bool = True


class SourceUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    type: SourceType | None = None
    url: str | None = Field(default=None, max_length=512)
    enabled: bool | None = None


class SourceRead(BaseModel):
    id: str
    name: str
    type: SourceType
    url: str
    enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True


class KeywordCreate(BaseModel):
    word: str = Field(..., max_length=255)
    enabled : bool = True


class KeywordUpdate(BaseModel):
    word: str | None = Field(default=None, max_length=255)
    enabled: bool | None = None


class KeywordRead(BaseModel):
    id: str
    word: str
    enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NewsItemRead(BaseModel):
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
        from_attributes = True


class PostRead(BaseModel):
    id: str
    news_id: str
    generated_text: str
    status: PostStatus
    published_at: datetime | None
    error_message: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class GenerateRequest(BaseModel):
    text: str = Field(..., min_length=10)


class GenerateResponse(BaseModel):
    generated_text: str


class ParseRssRequest(BaseModel):
    url: str = Field(..., max_length=512)


class ParsedNewsItem(BaseModel):
    title: str
    url: str | None
    summary: str
    source: str
    published_at: datetime
    raw_text: str | None


class ParseSaveResponse(BaseModel):
    parsed_count: int
    saved_count: int
    skipped_count: int


class TaskResponse(BaseModel):
    task_id: str
    status: str


class ParseTelegramRequest(BaseModel):
    username: str = Field(..., max_length=512)