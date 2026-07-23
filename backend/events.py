"""Fixtures related to historical events and their factories."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories.historical import HistoricalEventFactory


@pytest.fixture(scope="function")
def historical_event_factory(db_session: AsyncSession) -> type[HistoricalEventFactory]:
    """Fixture to provide a configured HistoricalEventFactory."""
    HistoricalEventFactory._meta.sqlalchemy_session = db_session
    return HistoricalEventFactory