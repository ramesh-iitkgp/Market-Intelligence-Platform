"""API tests for the Financial Reasoning Engine endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.dependencies import get_financial_reasoning_service
from backend.schemas.reasoning_schemas import ReasoningResult

pytestmark = pytest.mark.integration


def test_analyze_endpoint_success():
    """
    Test the POST /reasoning/analyze endpoint with a mocked service.
    This verifies the API layer wiring and request/response handling.
    """
    # 1. Arrange
    # Create a mock service that returns a predictable result
    mock_service = AsyncMock()
    mock_result = ReasoningResult(
        findings=[],
        uncertainties=["Test uncertainty"],
        risks=[],
        contradictions=[],
    )
    mock_service.generate_reasoning.return_value = mock_result

    # Override the dependency
    app.dependency_overrides[get_financial_reasoning_service] = lambda: mock_service

    # 2. Act
    client = TestClient(app)
    response = client.post("/api/v1/reasoning/analyze", json={"query_text": "test"})

    # 3. Assert
    assert response.status_code == 200
    data = response.json()
    assert data["uncertainties"] == ["Test uncertainty"]

    # Clean up the override
    app.dependency_overrides = {}