"""Service for combining and ranking similarity scores from multiple strategies."""

from __future__ import annotations

import logging
from collections import defaultdict

from backend.database.historical_models import HistoricalEvent
from backend.repositories.historical_repository import HistoricalRepository
from backend.schemas.similarity_schemas import (
    SimilarityExplanation,
    SimilarityResult,
    SimilarityScore,
)
from backend.services.similarity_service import SimilarityEngineService


class CompositeSimilarityService:
    """
    Combines scores from various strategies to produce a final ranked list.

    This service orchestrates the SimilarityEngine, applies weights to different
    scores, normalizes them, and generates the final, explainable results.
    """

    def __init__(
        self,
        similarity_engine: SimilarityEngineService,
        historical_repo: HistoricalRepository,
        logger: logging.Logger | None = None,
    ):
        self._similarity_engine = similarity_engine
        self._historical_repo = historical_repo
        self._logger = logger or logging.getLogger(__name__)
        # Weights can be made configurable
        self._weights = {"embedding": 0.6, "graph": 0.3, "entity": 0.1}

    async def find_and_rank_similar_events(
        self, query_event: HistoricalEvent, top_k: int
    ) -> list[SimilarityResult]:
        """
        Finds, scores, ranks, and explains historically similar events.
        """
        # 1. Get raw scores from all strategies
        scores_by_strategy = await self._similarity_engine.find_similar_events(
            query_event, top_k
        )

        # 2. Combine scores into a composite score for each event
        composite_scores = defaultdict(lambda: defaultdict(float))
        for strategy_name, scores in scores_by_strategy.items():
            weight = self._weights.get(strategy_name, 0.0)
            for event_id, score in scores:
                composite_scores[event_id][strategy_name] = score
                composite_scores[event_id]["overall"] += score * weight

        # 3. Sort events by the final composite score
        sorted_event_ids = sorted(
            composite_scores.keys(),
            key=lambda eid: composite_scores[eid]["overall"],
            reverse=True,
        )[:top_k]

        # 4. Fetch full event details and build the final response
        results = []
        for rank, event_id in enumerate(sorted_event_ids, 1):
            event = await self._historical_repo.get_by_id(event_id)
            if not event:
                continue

            scores = composite_scores[event_id]
            similarity_score = SimilarityScore(
                overall=scores["overall"],
                embedding=scores.get("embedding"),
                graph=scores.get("graph"),
                entity=scores.get("entity"),
            )

            # Explanation generation would be more sophisticated in a real system
            explanation = SimilarityExplanation(
                reason="This event is considered similar based on a combination of factors.",
                contributing_factors=[
                    f"{name.capitalize()} Similarity"
                    for name in scores_by_strategy
                    if name in scores
                ],
            )

            results.append(
                SimilarityResult(
                    rank=rank, score=similarity_score, event=event, explanation=explanation
                )
            )

        return results