"""Base classes and interfaces for the similarity strategy framework."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from backend.database.historical_models import HistoricalEvent


class SimilarityStrategy(ABC):
    """Abstract base class for all similarity calculation strategies."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The unique name of the strategy (e.g., 'embedding', 'graph')."""
        ...

    @abstractmethod
    async def calculate(
        self,
        query_event: HistoricalEvent,
        candidates: list[HistoricalEvent],
    ) -> list[tuple[int, float]]:
        """
        Calculate similarity scores for a list of candidate events.

        Returns a list of tuples, where each tuple contains the candidate
        event's ID and its similarity score (0.0 to 1.0) from this strategy.
        """
        ...