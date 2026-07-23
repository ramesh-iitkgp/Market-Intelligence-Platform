"""Fixtures for creating repository instances."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.historical_repository import HistoricalRepository
from backend.repositories.reaction_repository import ReactionRepository
from backend.repositories.statistics_repository import StatisticsRepository
from backend.repositories.timeline_repository import TimelineRepository


@pytest.fixture
def historical_repository(db_session: AsyncSession) -> HistoricalRepository:
    """Fixture to create a HistoricalRepository instance for unit tests."""
    return HistoricalRepository(db_session)


@pytest.fixture
def timeline_repository(db_session: AsyncSession) -> TimelineRepository:
    """Fixture to create a TimelineRepository instance for unit tests."""
    return TimelineRepository(db_session)


@pytest.fixture
def statistics_repository(db_session: AsyncSession) -> StatisticsRepository:
    """Fixture to create a StatisticsRepository instance for unit tests."""
    return StatisticsRepository(db_session)


@pytest.fixture
def reaction_repository(db_session: AsyncSession) -> ReactionRepository:
    """Fixture to create a ReactionRepository instance for unit tests."""
    return ReactionRepository(db_session)