"""Factories for creating historical data models for testing."""

from __future__ import annotations

from datetime import datetime, timezone

import factory
from factory.alchemy import SQLAlchemyModelFactory

from backend.database.historical_models import HistoricalEvent


class HistoricalEventFactory(SQLAlchemyModelFactory):
    """Factory for creating HistoricalEvent instances with traits."""

    class Meta:
        model = HistoricalEvent
        sqlalchemy_session_persistence = "commit"

    id = factory.Sequence(lambda n: n + 1)
    title = factory.Faker("sentence", nb_words=5)
    description = factory.Faker("paragraph")
    event_type = factory.Iterator(
        ["Monetary Policy", "Fiscal Policy", "M&A", "Commodity Price Move"]
    )
    category = factory.Iterator(
        ["Central Banks", "Government", "Corporate", "Commodities"]
    )
    importance = factory.Faker("pyint", min_value=1, max_value=5)
    country = factory.Faker("country_code")
    source = factory.Faker("company")
    occurred_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    version = 1

    class Params:
        high_importance = factory.Trait(importance=5)
        low_importance = factory.Trait(importance=1)

        rbi_event = factory.Trait(
            title="RBI Monetary Policy",
            category="Central Banks",
            country="IN",
            event_type="Monetary Policy",
        )

        budget_event = factory.Trait(
            title="Union Budget Announcement",
            category="Government",
            country="IN",
            event_type="Fiscal Policy",
        )