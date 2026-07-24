"""Core service for the Historical Similarity Engine."""

from __future__ import annotations

import logging

from backend.database.historical_models import HistoricalEvent
from backend.repositories.historical_repository import HistoricalRepository
from backend.services.similarity.base import SimilarityStrategy


class SimilarityEngineService:
    """
    Orchestrates the hybrid similarity search across multiple strategies.

    This service is the main entry point for finding historically similar events.
    It retrieves candidate events and then delegates scoring to a collection
    of registered similarity strategies.
    """

    def __init__(
        self,
        strategies: list[SimilarityStrategy],
        historical_repo: HistoricalRepository,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the engine with a list of scoring strategies.

        Args:
            strategies: A list of concrete SimilarityStrategy implementations.
            historical_repo: The repository for fetching historical event data.
            logger: An optional logger instance.
        """
        if not strategies:
            raise ValueError("At least one similarity strategy must be provided.")
        self._strategies = strategies
        self._historical_repo = historical_repo
        self._logger = logger or logging.getLogger(__name__)

    async def find_similar_events(
        self, query_event: HistoricalEvent, top_k: int = 10
    ) -> dict[str, list[tuple[int, float]]]:
        """
        Find and score similar events using all registered strategies.
        """
        # In a real implementation, candidate selection would be more sophisticated,
        # likely using an initial vector search to get a candidate set.
        # For now, we'll fetch recent events as candidates.
        candidates, _ = await self._historical_repo.search(limit=1000, offset=0)

        scores_by_strategy: dict[str, list[tuple[int, float]]] = {}
        for strategy in self._strategies:
            self._logger.info("Running similarity strategy: %s", strategy.name)
            scores = await strategy.calculate(query_event, candidates)
            scores_by_strategy[strategy.name] = scores

        return scores_by_strategy