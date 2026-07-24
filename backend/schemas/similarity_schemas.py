"""Pydantic schemas for the Historical Similarity Engine."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from backend.schemas.historical_schemas import HistoricalEventRead


class SimilarityExplanation(BaseModel):
    """Explains why two events are considered similar."""

    reason: str = Field(
        ..., description="A human-readable explanation for the similarity."
    )
    contributing_factors: list[str] = Field(
        [], description="Specific factors that contributed to the score."
    )


class SimilarityScore(BaseModel):
    """Represents a breakdown of similarity scores from different strategies."""

    overall: float = Field(..., ge=0.0, le=1.0)
    embedding: float | None = Field(None, ge=0.0, le=1.0)
    graph: float | None = Field(None, ge=0.0, le=1.0)
    timeline: float | None = Field(None, ge=0.0, le=1.0)
    entity: float | None = Field(None, ge=0.0, le=1.0)
    market_reaction: float | None = Field(None, ge=0.0, le=1.0)


class SimilarityResult(BaseModel):
    """Represents a single historically similar event and its analysis."""

    rank: int = Field(..., gt=0, description="The rank of this result.")
    score: SimilarityScore
    event: HistoricalEventRead
    explanation: SimilarityExplanation


class SimilaritySearchRequest(BaseModel):
    """Request model for initiating a historical similarity search."""

    event_id: int | None = Field(
        None, description="The ID of a recent event to find similarities for."
    )
    query_text: str | None = Field(
        None, description="A free-text description of an event to find similarities for."
    )
    top_k: int = Field(10, gt=0, le=50, description="The number of similar events to return.")


class SimilaritySearchResponse(BaseModel):
    """The final response containing a ranked list of similar historical events."""

    query_event: HistoricalEventRead | None = None
    query_text: str | None = None
    results: list[SimilarityResult]