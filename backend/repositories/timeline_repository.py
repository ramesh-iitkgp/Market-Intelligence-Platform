"""Repository for timeline-specific historical event queries."""

from __future__ import annotations

from datetime import datetime
from typing import Sequence

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from backend.database.historical_models import EventEntity, HistoricalEvent


class TimelineRepository:
    """Provides data access for timeline generation."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository with an async database session."""
        self._session = session

    async def get_previous_events(
        self, occurred_at: datetime, limit: int
    ) -> Sequence[HistoricalEvent]:
        """Retrieve a number of events that occurred before a given timestamp."""
        stmt = (
            select(HistoricalEvent)
            .options(selectinload(HistoricalEvent.entities).joinedload(EventEntity.entity))
            .where(HistoricalEvent.occurred_at < occurred_at)
            .order_by(HistoricalEvent.occurred_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        # Reverse to return in chronological order
        return result.scalars().unique().all()[::-1]

    async def get_next_events(
        self, occurred_at: datetime, limit: int
    ) -> Sequence[HistoricalEvent]:
        """Retrieve a number of events that occurred after a given timestamp."""
        stmt = (
            select(HistoricalEvent)
            .options(selectinload(HistoricalEvent.entities).joinedload(EventEntity.entity))
            .where(HistoricalEvent.occurred_at > occurred_at)
            .order_by(HistoricalEvent.occurred_at.asc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().unique().all()

    async def get_surrounding_events(
        self, event_id: int, window: int
    ) -> tuple[Sequence[HistoricalEvent], HistoricalEvent | None, Sequence[HistoricalEvent]]:
        """
        Retrieve events immediately preceding and following a specific event.

        Returns a tuple of (previous_events, target_event, next_events).
        """
        target_event_stmt = (
            select(HistoricalEvent)
            .options(
                selectinload(HistoricalEvent.entities).joinedload(EventEntity.entity),
                joinedload(HistoricalEvent.reactions),
            )
            .where(HistoricalEvent.id == event_id)
        )
        target_event_res = await self._session.execute(target_event_stmt)
        target_event = target_event_res.scalar_one_or_none()

        if not target_event:
            return [], None, []

        previous_events = await self.get_previous_events(
            target_event.occurred_at, window
        )
        next_events = await self.get_next_events(target_event.occurred_at, window)

        return previous_events, target_event, next_events

```

### Part 3: Timeline Engine

Now, I'll implement the `TimelineService`. This service will act as the core of the Timeline Engine, using both the `HistoricalRepository` and the new `TimelineRepository` to provide the capabilities you outlined. It will be responsible for the business logic of constructing timelines based on various criteria.

This new service will live in `backend/services/`.

```diff