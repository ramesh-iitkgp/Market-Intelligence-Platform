"""Pydantic schemas for historical event API data contracts."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


# --- Assumed Schemas from Existing Modules ---


class EntitySchema(BaseModel):
    """Represents a normalized entity (assumed from Phase 1/2)."""

    id: int
    name: str
    type: str

    model_config = {"from_attributes": True}


# --- Schemas for Phase 3 ---


class EventEntitySchema(BaseModel):
    """Represents the role of an entity within an event."""

    role: str
    entity: EntitySchema

    model_config = {"from_attributes": True}


class HistoricalReactionSchema(BaseModel):
    """Represents a market reaction to an event."""

    id: int
    asset: str
    asset_type: str
    reaction_period: str
    price_before: float
    price_after: float
    percentage_change: float
    volume_change: float | None = None
    volatility_change: float | None = None

    model_config = {"from_attributes": True}


class HistoricalSnapshotSchema(BaseModel):
    """Represents the serialized knowledge snapshot for an event."""

    id: int
    representation: dict
    version: int
    created_at: datetime

    model_config = {"from_attributes": True}


class HistoricalEventBase(BaseModel):
    """Base schema for a historical event, containing common fields."""

    title: str
    description: str
    event_type: str
    category: str
    importance: int
    country: str
    source: str
    occurred_at: datetime


class HistoricalEventRead(HistoricalEventBase):
    """Full historical event representation for API read operations."""

    id: int
    entities: list[EventEntitySchema] = []
    reactions: list[HistoricalReactionSchema] = []
    snapshot: HistoricalSnapshotSchema | None = None

    model_config = {"from_attributes": True}


class PaginatedHistoricalEventResponse(BaseModel):
    """Standard paginated response for lists of historical events."""

    total: int
    limit: int
    offset: int
    items: list[HistoricalEventRead]


class TimelineResponse(BaseModel):
    """Response model for a timeline centered around a specific event."""

    previous_events: list[HistoricalEventRead]
    target_event: HistoricalEventRead | None
    next_events: list[HistoricalEventRead]


class StatisticsReportSchema(BaseModel):
    """Response model for aggregated historical event statistics."""

    events_per_year: dict[str, int]
    top_categories: dict[str, int]
    top_countries: dict[str, int]
    top_event_types: dict[str, int]
    top_entities: dict[str, int]