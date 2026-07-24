"""Unit tests for the EvidenceAnalyzerService."""

from __future__ import annotations

from backend.database.historical_models import HistoricalEvent
from backend.schemas.rag_schemas import RAGContext, Source
from backend.services.reasoning.evidence_analyzer_service import EvidenceAnalyzerService
from tests.factories.rag import RetrievedItemFactory
from tests.factories.historical import HistoricalEventFactory


def test_analyze_structures_evidence_correctly():
    """
    Verify that the service correctly parses a RAGContext into a structured
    AnalyzedEvidence model.
    """
    # 1. Arrange
    service = EvidenceAnalyzerService()

    # Create mock retrieved items from different sources
    similar_event = HistoricalEventFactory.build()
    similar_item = RetrievedItemFactory(
        item=similar_event,
        evidence__source=Source.SIMILARITY_ENGINE,
        evidence__final_score=0.9,
        evidence__metadata={"explanation": "Test explanation"},
    )

    market_reaction_data = {"asset": "Nifty", "percentage_change": -1.5, "period": "1D"}
    reaction_item = RetrievedItemFactory(
        item=market_reaction_data,
        evidence__source=Source.MARKET_REACTION,
    )

    rag_context = RAGContext(
        query_text="test",
        retrieved_items=[similar_item, reaction_item],
    )

    # 2. Act
    analyzed_evidence = service.analyze(rag_context)

    # 3. Assert
    assert len(analyzed_evidence.similar_events) == 1
    assert analyzed_evidence.similar_events[0].event.id == similar_event.id
    assert analyzed_evidence.similar_events[0].similarity_score == 0.9
    assert len(analyzed_evidence.market_reactions) == 1
    assert analyzed_evidence.market_reactions[0].asset == "Nifty"
    assert analyzed_evidence.market_reactions[0].percentage_change == -1.5