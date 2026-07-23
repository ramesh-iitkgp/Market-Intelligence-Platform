"""Repository for accessing historical market reaction data."""

from __future__ import annotations

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.historical_models import HistoricalReaction


class ReactionRepository:
    """Provides data access for market reactions to historical events."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository with an async database session."""
        self._session = session

    async def add(self, reaction: HistoricalReaction) -> None:
        """Add a single reaction to the session."""
        self._session.add(reaction)

    async def get_reactions_for_event(self, event_id: int) -> Sequence[HistoricalReaction]:
        """Retrieve all market reactions associated with a specific event."""
        stmt = select(HistoricalReaction).where(HistoricalReaction.event_id == event_id)
        result = await self._session.execute(stmt)
        return result.scalars().all()