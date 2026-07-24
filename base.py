"""Base components for the Financial Reasoning Engine."""

from __future__ import annotations

from abc import ABC, abstractmethod

from backend.schemas.rag_schemas import RAGContext
from backend.schemas.reasoning_schemas import Finding


class ReasoningStrategy(ABC):
    """
    Abstract base class for a single reasoning strategy.

    Each strategy analyzes the RAG context from a specific angle (e.g., historical,
    market impact, risk) and produces a set of evidence-backed findings.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """A unique identifier for the strategy."""
        ...

    @abstractmethod
    async def analyze(self, context: RAGContext) -> list[Finding]:
        """Analyzes the RAG context and returns a list of findings."""
        ...