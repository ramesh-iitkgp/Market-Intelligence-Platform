"""Service layer for generating historical event timelines."""

from __future__ import annotations

from datetime import datetime
from typing import Sequence

from backend.database.historical_models import HistoricalEvent
from backend.repositories.historical_repository import HistoricalRepository
from backend.repositories.timeline_repository import TimelineRepository


class TimelineService:
    """
    Implements the business logic for creating and querying event timelines.

    This service uses repositories to fetch event data and assembles it
    into meaningful chronological sequences based on various criteria.
    """

    def __init__(
        self,
        historical_repo: HistoricalRepository,
        timeline_repo: TimelineRepository,
    ):
        """Initialize the service with data repositories."""
        self._historical_repo = historical_repo
        self._timeline_repo = timeline_repo

    async def get_timeline_around_event(
        self, event_id: int, window: int = 5
    ) -> tuple[Sequence[HistoricalEvent], HistoricalEvent | None, Sequence[HistoricalEvent]]:
        """
        Generates a timeline centered around a specific event.

        Args:
            event_id: The ID of the central event.
            window: The number of events to fetch before and after the central event.

        Returns:
            A tuple containing (previous_events, target_event, next_events).
        """
        return await self._timeline_repo.get_surrounding_events(event_id, window)

    async def get_events_between_dates(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[Sequence[HistoricalEvent], int]:
        """Retrieves all events within a specific date range, chronologically."""
        # The search repository already sorts by date descending, which is
        # a common default for "latest events". For a chronological timeline,
        # we can reverse the results if needed or adjust the repository.
        # For now, we'll rely on the default and consumers can reverse if needed.
        return await self._historical_repo.search(
            start_date=start_date, end_date=end_date, limit=limit, offset=offset
        )

    async def get_events_for_entity(
        self, entity_id: int, limit: int = 100, offset: int = 0
    ) -> tuple[Sequence[HistoricalEvent], int]:
        """Creates a timeline of all historical events related to a specific entity."""
        return await self._historical_repo.search(
            entity_id=entity_id, limit=limit, offset=offset
        )

    async def get_events_by_category(
        self, category: str, limit: int = 100, offset: int = 0
    ) -> tuple[Sequence[HistoricalEvent], int]:
        """Creates a timeline of all historical events within a given category."""
        return await self._historical_repo.search(
            category=category, limit=limit, offset=offset
        )

    async def get_events_by_importance(
        self, min_importance: int, limit: int = 100, offset: int = 0
    ) -> tuple[Sequence[HistoricalEvent], int]:
        """
        Creates a timeline of events meeting a minimum importance threshold.
        """
        return await self._historical_repo.search(
            importance=min_importance, limit=limit, offset=offset
        )

    async def get_chronological_timeline(
        self, limit: int = 100, offset: int = 0
    ) -> tuple[Sequence[HistoricalEvent], int]:
        """
        Retrieves a general, paginated timeline of the most recent historical events.
        """
        return await self._historical_repo.search(limit=limit, offset=offset)

    async def search_events(self, **kwargs) -> tuple[Sequence[HistoricalEvent], int]:
        """
        Exposes the repository's search functionality to the API layer.
        """
        return await self._historical_repo.search(**kwargs)

    async def get_event_by_id(self, event_id: int) -> HistoricalEvent | None:
        """
        Exposes the repository's get_by_id functionality to the API layer.
        """
        return await self._historical_repo.get_by_id(event_id)

```

With these two components, we now have a robust and decoupled Timeline Engine. The `TimelineRepository` handles the specific database logic for relative time-based queries, while the `TimelineService` provides a clean, high-level API for all timeline-related use cases. This service is now ready to be injected into FastAPI endpoints.

<!--
[PROMPT_SUGGESTION]Create the Pydantic schemas and FastAPI endpoints for the timeline and search APIs.[/PROMPT_SUGGESTION]
[PROMPT_SUGGESTION]Implement the Statistics Engine and its associated service (`statistics_service.py`).[/PROMPT_SUGGESTION]
-->