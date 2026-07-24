"""Similarity strategy based on the timeline of preceding events."""

from __future__ import annotations

from backend.database.historical_models import HistoricalEvent
from backend.repositories.timeline_repository import TimelineRepository
from backend.services.similarity.base import SimilarityStrategy


class TimelineSimilarityStrategy(SimilarityStrategy):
    """
    Calculates similarity based on the sequence of events preceding an event.

    This strategy compares the "timeline leading up to" two different events.
    If the sequence of event types or categories is similar, it suggests that
    the contextual background of the events might be similar.
    """

    def __init__(self, timeline_repo: TimelineRepository, window_size: int = 5):
        """
        Initialize the strategy.

        Args:
            timeline_repo: Repository to fetch timeline data.
            window_size: The number of preceding events to consider in the timeline.
        """
        self._timeline_repo = timeline_repo
        self._window_size = window_size

    @property
    def name(self) -> str:
        return "timeline"

    async def calculate(
        self,
        query_event: HistoricalEvent,
        candidates: list[HistoricalEvent],
    ) -> list[tuple[int, float]]:
        query_timeline = await self._timeline_repo.get_previous_events(
            query_event.occurred_at, self._window_size
        )
        query_timeline_categories = [event.category for event in query_timeline]

        if not query_timeline_categories:
            return []

        scores = []
        for candidate in candidates:
            if candidate.id == query_event.id:
                continue

            candidate_timeline = await self._timeline_repo.get_previous_events(
                candidate.occurred_at, self._window_size
            )
            candidate_timeline_categories = [event.category for event in candidate_timeline]

            # Use a simple sequence matching score
            match_count = sum(1 for i, cat in enumerate(query_timeline_categories) if i < len(candidate_timeline_categories) and cat == candidate_timeline_categories[i])
            score = match_count / self._window_size if self._window_size > 0 else 0.0
            scores.append((candidate.id, score))

        return scores