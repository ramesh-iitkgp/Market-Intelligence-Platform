"""SQLAlchemy models for the historical event database."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func

if TYPE_CHECKING:
    from .entity_models import Entity  # Assuming entities are in entity_models.py


class Base(DeclarativeBase):
    """Base for historical models."""


class HistoricalEvent(Base):
    """Represents a significant historical market or geopolitical event."""

    __tablename__ = "historical_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    importance: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    country: Mapped[str] = mapped_column(String(100), index=True)
    source: Mapped[str] = mapped_column(String(255))

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Vectorization preparation
    text_hash: Mapped[str | None] = mapped_column(String(64))
    embedding_status: Mapped[str] = mapped_column(
        String(20), server_default="pending", nullable=False
    )
    embedding_version: Mapped[int | None] = mapped_column(Integer)
    embedding_model: Mapped[str | None] = mapped_column(String(100))

    # For optimistic locking
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="1", default=1
    )

    entities: Mapped[list[EventEntity]] = relationship(
        "EventEntity", back_populates="event", cascade="all, delete-orphan"
    )
    reactions: Mapped[list[HistoricalReaction]] = relationship(
        "HistoricalReaction", back_populates="event", cascade="all, delete-orphan"
    )
    snapshot: Mapped[HistoricalSnapshot | None] = relationship(
        "HistoricalSnapshot",
        back_populates="event",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __mapper_args__ = {"version_id_col": version}

    def __repr__(self) -> str:
        return f"<HistoricalEvent(id={self.id}, title='{self.title}')>"


class EventEntity(Base):
    """Associates an entity with a historical event and defines its role."""

    __tablename__ = "event_entities"
    __table_args__ = (UniqueConstraint("event_id", "entity_id"),)

    event_id: Mapped[int] = mapped_column(
        ForeignKey("historical_events.id"), primary_key=True
    )
    entity_id: Mapped[int] = mapped_column(
        ForeignKey("entities.id"), primary_key=True
    )  # Assumes entities.id
    role: Mapped[str] = mapped_column(String(50), nullable=False)

    event: Mapped[HistoricalEvent] = relationship(
        "HistoricalEvent", back_populates="entities"
    )
    entity: Mapped[Entity] = relationship("Entity")  # Assumes a simple Entity model

    def __repr__(self) -> str:
        return f"<EventEntity(event_id={self.event_id}, entity_id={self.entity_id}, role='{self.role}')>"


class HistoricalReaction(Base):
    """Records the market reaction to a historical event for a specific asset."""

    __tablename__ = "historical_reactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("historical_events.id"), nullable=False, index=True
    )
    asset: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    reaction_period: Mapped[str] = mapped_column(String(10), nullable=False)

    price_before: Mapped[float] = mapped_column(Float, nullable=False)
    price_after: Mapped[float] = mapped_column(Float, nullable=False)
    percentage_change: Mapped[float] = mapped_column(Float, nullable=False)
    volume_change: Mapped[float | None] = mapped_column(Float)
    volatility_change: Mapped[float | None] = mapped_column(Float)

    event: Mapped[HistoricalEvent] = relationship(
        "HistoricalEvent", back_populates="reactions"
    )

    def __repr__(self) -> str:
        return f"<HistoricalReaction(id={self.id}, asset='{self.asset}', event_id={self.event_id})>"


class HistoricalSnapshot(Base):
    """Stores a serialized knowledge representation of a historical event."""

    __tablename__ = "historical_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("historical_events.id"), unique=True, nullable=False
    )
    representation: Mapped[dict] = mapped_column(JSONB, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    event: Mapped[HistoricalEvent] = relationship(
        "HistoricalEvent", back_populates="snapshot"
    )

    def __repr__(self) -> str:
        return f"<HistoricalSnapshot(id={self.id}, event_id={self.event_id}, version={self.version})>"


# Assuming a simple Entity model exists for relationships.
# If it doesn't, it would look something like this:
#
# class Entity(Base):
#     __tablename__ = "entities"
#     id: Mapped[int] = mapped_column(primary_key=True)
#     name: Mapped[str] = mapped_column(String, unique=True, index=True)
#     type: Mapped[str] = mapped_column(String, index=True)
#     ...

```

### Part 2 & 4: Repositories and Historical Search

Next, I'll implement the repository layer for data access. This `HistoricalRepository` will encapsulate all database interactions for historical events, supporting insertion, filtering, and searching as specified.

This new file will live in the `backend/repositories/` directory.

```diff