"""Pydantic schemas for Knowledge Graph API data contracts."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from backend.database.graph_models import EntityType, RelationshipType


class EntityAliasRead(BaseModel):
    """Schema for reading an entity alias."""

    alias: str

    model_config = {"from_attributes": True}


class EntityNodeRead(BaseModel):
    """Schema for reading a full entity node, including its aliases."""

    id: uuid.UUID
    entity_type: EntityType
    canonical_name: str
    description: str | None = None
    metadata: dict | None = None
    aliases: list[EntityAliasRead] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NeighborNodeRead(BaseModel):
    """A simplified schema for a node when returned as a neighbor."""

    id: uuid.UUID
    entity_type: EntityType
    canonical_name: str
    description: str | None = None

    model_config = {"from_attributes": True}


class NeighborsResponse(BaseModel):
    """Response model for a node and its direct neighbors."""

    node: EntityNodeRead
    neighbors: list[NeighborNodeRead]


class GraphBuildRequest(BaseModel):
    """Request model to trigger a graph build from a historical event."""

    event_id: int = Field(
        ..., description="The ID of the historical event to process."
    )


class GraphBuildResponse(BaseModel):
    """Response model confirming the graph build process was initiated."""

    status: str
    message: str
    event_id: int