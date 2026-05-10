import uuid
import enum
from datetime import datetime

from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ── Перечисления (допустимые значения полей) ─────────────
class SourceType(str, enum.Enum):
    site     = "site"   # обычный сайт / RSS
    telegram = "tg"     # Telegram-канал


class PostStatus(str, enum.Enum):
    new       = "new"        # только что создан
    generated = "generated"  # текст сгенерирован AI
    published = "published"  # опубликован в Telegram
    failed    = "failed"     # ошибка на каком-то шаге


# ── Таблица: источники новостей ───────────────────────────
class Source(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str]    = mapped_column(String(255))
    type: Mapped[SourceType] = mapped_column(
        SAEnum(SourceType), default=SourceType.site,
    )
    url: Mapped[str]     = mapped_column(String(512))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow,
    )

    # Связь: один источник → много новостей
    news_items: Mapped[list["NewsItem"]] = relationship(
        back_populates="source_rel",
    )


# ── Таблица: новости ──────────────────────────────────────
class NewsItem(Base):
    __tablename__ = "news_items"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    title:        Mapped[str]           = mapped_column(String(512))
    url:          Mapped[str | None]    = mapped_column(String(512), nullable=True)
    summary:      Mapped[str]           = mapped_column(Text)
    raw_text:     Mapped[str | None]    = mapped_column(Text, nullable=True)
    source:       Mapped[str]           = mapped_column(String(255))
    source_id:    Mapped[str | None]    = mapped_column(
        String(36), ForeignKey("sources.id"), nullable=True,
    )
    published_at: Mapped[datetime]      = mapped_column(DateTime)
    created_at:   Mapped[datetime]      = mapped_column(
        DateTime, default=datetime.utcnow,
    )

    source_rel: Mapped["Source"]       = relationship(back_populates="news_items")
    post:       Mapped["Post | None"]  = relationship(back_populates="news_item")


# ── Таблица: сгенерированные посты ───────────────────────
class Post(Base):
    __tablename__ = "posts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    news_id:        Mapped[str]           = mapped_column(
        String(36), ForeignKey("news_items.id"),
    )
    generated_text: Mapped[str]           = mapped_column(Text)
    status:         Mapped[PostStatus]    = mapped_column(
        SAEnum(PostStatus), default=PostStatus.new,
    )
    published_at:   Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True,
    )
    error_message:  Mapped[str | None]    = mapped_column(Text, nullable=True)
    created_at:     Mapped[datetime]      = mapped_column(
        DateTime, default=datetime.utcnow,
    )

    news_item: Mapped["NewsItem"] = relationship(back_populates="post")


# ── Таблица: ключевые слова для фильтрации ────────────────
class Keyword(Base):
    __tablename__ = "keywords"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    word:       Mapped[str]  = mapped_column(String(255), unique=True)
    enabled:    Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow,
    )
