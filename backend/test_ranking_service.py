"""Unit tests for the RAG RankingService."""

from __future__ import annotations

import pytest

from backend.schemas.rag_schemas import Source
from backend.services.rag.ranking import RankingService
from tests.factories.rag import RetrievedItemFactory


def test_rank_and_filter_sorts_by_final_score():
    """Verify that items are sorted correctly based on weighted score."""
    service = RankingService()
    # Item 2 has a higher initial score but a lower weight, so it should end up last.
    item1 = RetrievedItemFactory(
        evidence__source=Source.SIMILARITY_ENGINE, evidence__score=0.8
    )  # weight 1.0 -> final 0.8
    item2 = RetrievedItemFactory(
        evidence__source=Source.GRAPH_NEIGHBORHOOD, evidence__score=0.9
    )  # weight 0.8 -> final 0.72

    items = [item2, item1]
    ranked_items = service.rank_and_filter(items)

    assert len(ranked_items) == 2
    assert ranked_items[0].evidence.source == Source.SIMILARITY_ENGINE
    assert ranked_items[1].evidence.source == Source.GRAPH_NEIGHBORHOOD
    assert ranked_items[0].evidence.final_score > ranked_items[1].evidence.final_score


def test_rank_and_filter_deduplicates_items():
    """Verify that items with duplicate content are removed, keeping the highest-scoring one."""
    service = RankingService()
    content = "Duplicate content"

    # Create two items with the same content but different scores
    item1_high_score = RetrievedItemFactory(
        evidence__content=content, evidence__score=0.9
    )
    item2_low_score = RetrievedItemFactory(
        evidence__content=content, evidence__score=0.5
    )
    item3_unique = RetrievedItemFactory(evidence__content="Unique content")

    items = [item2_low_score, item3_unique, item1_high_score]
    ranked_items = service.rank_and_filter(items)

    assert len(ranked_items) == 2
    # Check that the one with the higher score was kept
    assert any(
        item.evidence.score == 0.9 for item in ranked_items if item.evidence.content == content
    )
    assert not any(
        item.evidence.score == 0.5 for item in ranked_items if item.evidence.content == content
    )