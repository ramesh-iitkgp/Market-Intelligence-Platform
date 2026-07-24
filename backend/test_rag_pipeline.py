"""End-to-end integration tests for the RAG pipeline."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.main import app  # Assuming your FastAPI app is in main.py
from backend.schemas.rag_schemas import RAGContext
from backend.schemas.similarity_schemas import (
    SimilarityExplanation,
    SimilarityResult,
    SimilarityScore,
)
from tests.factories.graph import EntityNodeFactory, RelationshipEdgeFactory
from tests.factories.historical import HistoricalEventFactory

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_rag_full_pipeline(
    integration_db_session: AsyncSession,
    historical_event_factory: type[HistoricalEventFactory],
    entity_node_factory: type[EntityNodeFactory],
    relationship_edge_factory: type[RelationshipEdgeFactory],
):
    """
    Tests the full /rag/context pipeline from request to response.

    This test verifies that retrieval, ranking, assembly, and prompt building
    work together correctly.
    """
    # 1. Arrange: Set up the data
    # Query Event and its entities
    query_event = historical_event_factory(title="Query Event")
    company_a_node = entity_node_factory(canonical_name="Company A")
    # Link historical event entity to graph node via name
    query_event.entities = [
        {"entity": {"name": "Company A", "type": "COMPANY"}, "role": "subject"}
    ]

    # Similar Event (to be returned by mocked similarity engine)
    similar_event = historical_event_factory(title="Similar Event")

    # Timeline Context Events
    preceding_event = historical_event_factory(title="Preceding Event", occurred_at=query_event.occurred_at - timedelta(days=1))

    # Graph Context
    company_b_node = entity_node_factory(canonical_name="Company B")
    relationship_edge_factory(source_node=company_a_node, target_node=company_b_node)

    await integration_db_session.commit()

    # Mock the similarity service to return a predictable result
    mock_similarity_result = [
        SimilarityResult(
            rank=1,
            score=SimilarityScore(overall=0.9, embedding=0.9),
            event=similar_event,
            explanation=SimilarityExplanation(reason="High semantic similarity."),
        )
    ]

    # 2. Act: Call the API endpoint
    with patch(
        "backend.services.composite_similarity_service.CompositeSimilarityService.find_and_rank_similar_events",
        new=AsyncMock(return_value=mock_similarity_result),
    ):
        client = TestClient(app)
        response = client.post(
            "/rag/context", json={"event_id": query_event.id, "top_k": 1}
        )

    # 3. Assert
    assert response.status_code == 200
    rag_context = RAGContext.model_validate(response.json())

    # Assert Query Event
    assert rag_context.query_event.id == query_event.id

    # Assert Similarity Context
    assert len(rag_context.similar_events) == 1
    assert rag_context.similar_events[0].item["id"] == similar_event.id

    # Assert Timeline Context
    assert len(rag_context.timeline_context) == 1
    assert rag_context.timeline_context[0].item["id"] == preceding_event.id

    # Assert Graph Context
    assert len(rag_context.graph_neighborhood) == 1
    assert rag_context.graph_neighborhood[0].item["canonical_name"] == "Company B"

    # Assert Diagnostics
    assert rag_context.diagnostics is not None
    assert rag_context.diagnostics.total_tokens_used > 0
    assert rag_context.diagnostics.items_included > 0