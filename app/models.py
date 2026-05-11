"""SQLAlchemy-модели источников, новостей, постов и ключевых слов."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей."""

    pass


class SourceType(str, enum.Enum):
    """Тип источника новостей."""

    site = "site"
    telegram = "tg"


class PostStatus(str, enum.Enum):
    """Статус сгенерированного Telegram-поста."""

    new = "new"
    generated = "generated"
    published = "published"
    failed = "failed"


class Source(Base):
    """Источник новостей: RSS-сайт или Telegram-канал."""

    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[SourceType] = mapped_column(
        SAEnum(SourceType),
        default=SourceType.site,
    )
    url: Mapped[str] = mapped_column(String(512))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    news_items: Mapped[list["NewsItem"]] = relationship(
        back_populates="source_rel",
    )


class NewsItem(Base):
    """Новость, полученная из внешнего источника."""

    __tablename__ = "news_items"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    title: Mapped[str] = mapped_column(String(512))
    url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    summary: Mapped[str] = mapped_column(Text)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(255))
    source_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("sources.id"),
        nullable=True,
    )
    published_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    source_rel: Mapped["Source"] = relationship(back_populates="news_items")
    post: Mapped["Post | None"] = relationship(back_populates="news_item")


class Post(Base):
    """Telegram-пост, сгенерированный на основе новости."""

    __tablename__ = "posts"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    news_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("news_items.id"),
    )
    generated_text: Mapped[str] = mapped_column(Text)
    status: Mapped[PostStatus] = mapped_column(
        SAEnum(PostStatus),
        default=PostStatus.new,
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    news_item: Mapped["NewsItem"] = relationship(back_populates="post")


class Keyword(Base):
    """Ключевое слово для фильтрации новостей."""

    __tablename__ = "keywords"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    word: Mapped[str] = mapped_column(String(255), unique=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )