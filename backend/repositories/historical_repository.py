"""Repository for accessing historical event data."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Sequence

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, joinedload, selectinload

from backend.database.historical_models import EventEntity, HistoricalEvent


class HistoricalRepository:
    """Provides data access for historical events and their relationships."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository with an async database session."""
        self._session = session

    async def add(self, event: HistoricalEvent) -> None:
        """Add a single historical event to the session."""
        self._session.add(event)

    async def bulk_add(self, events: list[HistoricalEvent]) -> None:
        """Add multiple historical events in bulk."""
        self._session.add_all(events)

    async def get_by_id(self, event_id: int) -> HistoricalEvent | None:
        """Retrieve a single event by its ID, with related entities."""
        stmt = (
            select(HistoricalEvent)
            .options(
                selectinload(HistoricalEvent.entities).joinedload(EventEntity.entity),
                joinedload(HistoricalEvent.reactions),
                joinedload(HistoricalEvent.snapshot),
            )
            .where(HistoricalEvent.id == event_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def search(
        self,
        *,
        limit: int,
        offset: int,
        keyword: str | None = None,
        entity_id: int | None = None,
        country: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        importance: int | None = None,
        event_type: str | None = None,
        category: str | None = None,
    ) -> tuple[Sequence[HistoricalEvent], int]:
        """
        Search and filter historical events with pagination.

        Supports combined filters for powerful and flexible querying.
        """
        stmt = (
            select(HistoricalEvent, func.count(HistoricalEvent.id).over())
            .options(selectinload(HistoricalEvent.entities).joinedload(EventEntity.entity))
            .order_by(HistoricalEvent.occurred_at.desc())
        )

        filters = self._build_filters(
            keyword=keyword,
            entity_id=entity_id,
            country=country,
            start_date=start_date,
            end_date=end_date,
            importance=importance,
            event_type=event_type,
            category=category,
        )
        if filters:
            stmt = stmt.where(and_(*filters))

        # Handle entity lookup via a subquery to avoid cartesian products in main query
        if entity_id is not None:
            stmt = stmt.join(HistoricalEvent.entities).where(
                EventEntity.entity_id == entity_id
            )
            # Use contains_eager to load the specific entity relationship
            stmt = stmt.options(contains_eager(HistoricalEvent.entities))

        paginated_stmt = stmt.limit(limit).offset(offset)

        result = await self._session.execute(paginated_stmt)
        rows = result.unique().all()
        events = [row[0] for row in rows]
        total_count = rows[0][1] if rows else 0
        return events, total_count

    def _build_filters(self, **kwargs: Any) -> list[Any]:
        """Construct a list of SQLAlchemy filter conditions from search parameters."""
        filters = []
        if (keyword := kwargs.get("keyword")):
            filters.append(
                or_(
                    HistoricalEvent.title.ilike(f"%{keyword}%"),
                    HistoricalEvent.description.ilike(f"%{keyword}%"),
                )
            )
        if (country := kwargs.get("country")):
            filters.append(HistoricalEvent.country == country)
        if (start_date := kwargs.get("start_date")):
            filters.append(HistoricalEvent.occurred_at >= start_date)
        if (end_date := kwargs.get("end_date")):
            filters.append(HistoricalEvent.occurred_at <= end_date)
        if (importance := kwargs.get("importance")) is not None:
            filters.append(HistoricalEvent.importance >= importance)
        if (event_type := kwargs.get("event_type")):
            filters.append(HistoricalEvent.event_type == event_type)
        if (category := kwargs.get("category")):
            filters.append(HistoricalEvent.category == category)

        return filters

```

### Next Steps

This is a substantial first step that lays a solid foundation for Phase 3. We have defined the data structures and the primary access patterns. The next logical steps would be to build the `TimelineService`, `StatisticsService`, and the corresponding FastAPI endpoints that will consume this repository.

This modular implementation ensures that as we build out the remaining parts—Timeline Engine, Statistics, Importers, and APIs—we will have a clean, decoupled, and testable architecture.

Let me know when you're ready to proceed with the service layer and API endpoints!

<!--
[PROMPT_SUGGESTION]Implement the Timeline Engine and its associated repository and service (`timeline_service.py`).[/PROMPT_SUGGESTION]
[PROMPT_SUGGESTION]Create the Pydantic schemas and FastAPI endpoints for the historical event search API (`/historical/search`).[/PROMPT_SUGGESTION]
-->