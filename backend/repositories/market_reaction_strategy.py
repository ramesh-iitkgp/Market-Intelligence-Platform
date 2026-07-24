"""Similarity strategy based on historical market reactions."""

from __future__ import annotations

import math

from backend.database.historical_models import HistoricalEvent, HistoricalReaction
from backend.repositories.reaction_repository import ReactionRepository
from backend.services.similarity.base import SimilarityStrategy


class MarketReactionSimilarityStrategy(SimilarityStrategy):
    """
    Calculates similarity based on the market reaction to historical events.

    This strategy compares quantitative data, such as the percentage change
    of a key index (e.g., Nifty) following two different events.
    """

    def __init__(self, reaction_repo: ReactionRepository):
        self._reaction_repo = reaction_repo

    @property
    def name(self) -> str:
        return "market_reaction"

    async def calculate(
        self,
        query_event: HistoricalEvent,
        candidates: list[HistoricalEvent],
    ) -> list[tuple[int, float]]:
        query_reactions = await self._reaction_repo.get_reactions_for_event(
            query_event.id
        )
        query_reaction_map = {r.asset: r for r in query_reactions}

        if not query_reaction_map:
            return []

        scores = []
        for candidate in candidates:
            if candidate.id == query_event.id:
                continue

            candidate_reactions = await self._reaction_repo.get_reactions_for_event(
                candidate.id
            )
            candidate_reaction_map = {r.asset: r for r in candidate_reactions}

            # For now, we'll use a simple comparison on a primary asset.
            # A more advanced version could compare multiple assets.
            primary_asset = "Nifty"
            query_primary_reaction = query_reaction_map.get(primary_asset)
            candidate_primary_reaction = candidate_reaction_map.get(primary_asset)

            if query_primary_reaction and candidate_primary_reaction:
                diff = abs(query_primary_reaction.percentage_change - candidate_primary_reaction.percentage_change)
                # Use an exponential decay function to map difference to a 0-1 score.
                # A smaller difference results in a higher score.
                score = math.exp(-0.5 * diff)
                scores.append((candidate.id, score))

        return scores