"""Unit tests for the HistoricalRepository."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.historical_models import HistoricalEvent
from backend.repositories.historical_repository import HistoricalRepository
from tests.factories.historical import HistoricalEventFactory

pytestmark = pytest.mark.asyncio


async def test_get_by_id_returns_event(
    db_session: AsyncSession, historical_event_factory: type[HistoricalEventFactory]
):
    """Verify that get_by_id retrieves the correct event."""
    event = historical_event_factory(title="Specific Event")
    await db_session.commit()

    repo = HistoricalRepository(db_session)
    retrieved_event = await repo.get_by_id(event.id)

    assert retrieved_event is not None
    assert retrieved_event.id == event.id
    assert retrieved_event.title == "Specific Event"


async def test_get_by_id_returns_none_for_invalid_id(
    db_session: AsyncSession,
):
    """Verify that get_by_id returns None for a non-existent ID."""
    repo = HistoricalRepository(db_session)
    event = await repo.get_by_id(999)

    assert event is None


async def test_search_with_keyword(
    db_session: AsyncSession, historical_event_factory: type[HistoricalEventFactory]
):
    """Verify keyword search against title and description."""
    historical_event_factory(description="A key event about Crude Oil.")
    await db_session.commit()

    repo = HistoricalRepository(db_session)
    events, total = await repo.search(limit=10, offset=0, keyword="Crude Oil")

    assert total == 1
    assert len(events) == 1
    assert "Crude Oil" in events[0].description


async def test_search_with_date_range(
    db_session: AsyncSession, historical_event_factory: type[HistoricalEventFactory]
):
    """Verify search within a specific date range."""
    now = datetime.now(timezone.utc)
    event_in_range = historical_event_factory(occurred_at=now - timedelta(days=5))
    historical_event_factory(occurred_at=now - timedelta(days=20))
    await db_session.commit()

    repo = HistoricalRepository(db_session)
    events, total = await repo.search(
        limit=10, offset=0, start_date=now - timedelta(days=10), end_date=now
    )

    assert total == 1
    assert len(events) == 1
    assert events[0].id == event_in_range.id


async def test_search_with_category(
    db_session: AsyncSession, historical_event_factory: type[HistoricalEventFactory]
):
    """Verify filtering by event category."""
    historical_event_factory(category="Corporate", title="Adani Acquires Company")
    await db_session.commit()

    repo = HistoricalRepository(db_session)
    events, total = await repo.search(limit=10, offset=0, category="Corporate")

    assert total == 1
    assert len(events) == 1
    assert "Adani Acquires Company" in events[0].title


async def test_search_with_pagination(
    db_session: AsyncSession, historical_event_factory: type[HistoricalEventFactory]
):
    """Verify that limit and offset are correctly applied."""
    # Create a known number of events
    historical_event_factory.create_batch(4)
    await db_session.commit()

    repo = HistoricalRepository(db_session)

    # Get first page
    events_page1, total1 = await repo.search(limit=2, offset=0)
    assert total1 == 4
    assert len(events_page1) == 2

    # Get second page
    events_page2, total2 = await repo.search(limit=2, offset=2)
    assert total2 == 4
    assert len(events_page2) == 2

    # Ensure pages are different
    assert events_page1[0].id != events_page2[0].id


async def test_search_with_combined_filters(
    db_session: AsyncSession, historical_event_factory: type[HistoricalEventFactory]
):
    """Verify that multiple filters can be combined correctly."""
    # Correctly apply traits using boolean flags
    target_event = historical_event_factory(high_importance=True, country="IN")
    historical_event_factory(low_importance=True, country="IN")
    historical_event_factory(high_importance=True, country="US")
    await db_session.commit()

    repo = HistoricalRepository(db_session)
    events, total = await repo.search(
        limit=10, offset=0, country="IN", importance=5
    )

    assert total == 1
    assert len(events) == 1
    assert events[0].id == target_event.id