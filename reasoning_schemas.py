"""Pydantic schemas for the Financial Reasoning Engine."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from backend.schemas.rag_schemas import RAGQuery


class ReasoningQuery(RAGQuery):
    """Defines the input for a financial reasoning request."""

    # In the future, we can add specific reasoning parameters here.
    pass


class EvidenceSource(BaseModel):
    """Represents a piece of evidence backing a finding."""

    source_type: str = Field(
        description="The type of the source (e.g., 'historical_event', 'graph_relationship')."
    )
    content: str = Field(description="The textual content of the evidence.")
    score: float | None = Field(
        None, description="The relevance score of the evidence, if applicable."
    )
    metadata: dict = Field(default_factory=dict, description="Additional source metadata.")


class Finding(BaseModel):
    """Represents a single, evidence-backed conclusion from a reasoning strategy."""

    strategy: str = Field(description="The name of the strategy that generated the finding.")
    conclusion: str = Field(description="The reasoned conclusion or insight.")
    evidence: list[EvidenceSource] = Field(
        description="A list of evidence items supporting the conclusion."
    )
    confidence: float = Field(
        description="A score from 0.0 to 1.0 indicating the confidence in the conclusion."
    )
    reasoning_chain: list[str] = Field(
        default_factory=list,
        description="A step-by-step explanation of how the conclusion was derived from the evidence.",
    )


class ReasoningResult(BaseModel):
    """The final, structured output of the Financial Reasoning Engine."""

    findings: list[Finding] = Field(description="A list of all generated findings.")
    assumptions: list[str] = Field(
        default_factory=list, description="Assumptions made during the reasoning process."
    )
    contradictions: list[str] = Field(
        default_factory=list, description="Any conflicting evidence or findings detected."
    )
    uncertainties: list[str] = Field(
        default_factory=list, description="Key areas of uncertainty or missing information."
    )