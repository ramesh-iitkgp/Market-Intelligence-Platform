"""Pydantic schemas for validating structured AI model outputs."""

from __future__ import annotations

from pydantic import BaseModel, Field, conlist

from backend.database.graph_models import EntityType, RelationshipType


class ExtractedEntity(BaseModel):
    """Schema for a single entity extracted by the AI model."""

    name: str = Field(..., description="The canonical name of the entity.")
    type: EntityType = Field(..., description="The normalized type of the entity.")


class ExtractedRelationship(BaseModel):
    """Schema for a single relationship extracted by the AI model."""

    source: str = Field(
        ..., description="The name of the source entity for the relationship."
    )
    target: str = Field(
        ..., description="The name of the target entity for the relationship."
    )
    type: RelationshipType = Field(
        ..., description="The type of the relationship."
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="The model's confidence in the relationship."
    )
    evidence: str = Field(
        ..., description="The sentence or phrase from the text supporting the relationship."
    )


class GraphExtractionResult(BaseModel):
    """The root schema for the entire graph extraction from the AI model."""

    entities: conlist(ExtractedEntity, min_length=1)
    relationships: list[ExtractedRelationship]