"""Unit tests for the RAG RetrievalService."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.schemas.rag_schemas import RAGQuery
from backend.services.rag.retrieval import RetrievalService
from tests.factories.rag import RetrievedItemFactory

pytestmark = pytest.mark.asyncio


async def test_retrieval_service_runs_all_strategies():
    """Verify the service calls all registered strategies and aggregates results."""
    # 1. Arrange: Create mock strategies
    strategy1 = AsyncMock()
    strategy1.retrieve.return_value = [RetrievedItemFactory()]

    strategy2 = AsyncMock()
    strategy2.retrieve.return_value = [
        RetrievedItemFactory(),
        RetrievedItemFactory(),
    ]

    # 2. Act: Run the service
    service = RetrievalService(strategies=[strategy1, strategy2])
    query = RAGQuery(query_text="test")
    results = await service.retrieve(query)

    # 3. Assert
    # Check that each strategy was called once with the correct query
    strategy1.retrieve.assert_called_once_with(query)
    strategy2.retrieve.assert_called_once_with(query)

    # Check that the results from all strategies were aggregated
    assert len(results) == 3