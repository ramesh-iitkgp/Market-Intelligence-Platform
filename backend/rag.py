"""Factories for creating RAG-related objects for testing."""

from __future__ import annotations

import factory

from backend.schemas.rag_schemas import Evidence, RetrievedItem, Source


class EvidenceFactory(factory.Factory):
    """Factory for creating Evidence instances."""

    class Meta:
        model = Evidence

    source = factory.Iterator([Source.SIMILARITY_ENGINE, Source.TIMELINE_CONTEXT])
    content = factory.Faker("sentence")
    score = factory.Faker("pyfloat", min_value=0.1, max_value=1.0)
    final_score = 0.0
    metadata = factory.Dict({})


class RetrievedItemFactory(factory.Factory):
    """Factory for creating RetrievedItem instances."""

    class Meta:
        model = RetrievedItem

    evidence = factory.SubFactory(EvidenceFactory)
    # The 'item' attribute would be a factory for a SQLAlchemy model in integration tests
    item = factory.LazyFunction(dict)