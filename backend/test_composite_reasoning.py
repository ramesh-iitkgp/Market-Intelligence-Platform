"""Unit tests for the composite reasoning and scenario generation services."""

from __future__ import annotations
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.schemas.reasoning_schemas import (
    AnalyzedEvidence,
    Finding,
    ReasoningResult,
)
from backend.services.reasoning_service import ReasoningEngineService
from backend.services.reasoning.scenario_generation_service import (
    ScenarioGenerationService,
)

pytestmark = pytest.mark.asyncio


async def test_reasoning_engine_synthesizes_contradictions():
    """Verify the engine detects contradictory market impact findings."""
    # 1. Arrange
    # Create findings suggesting opposite market movements for the same asset
    positive_finding = Finding(
        strategy="Market Impact",
        conclusion="Positive impact on Nifty",
        evidence=[
            {
                "source_type": "market_reaction",
                "content": "",
                "metadata": {"asset": "Nifty", "percentage_change": 1.5},
            }
        ],
        confidence=0.7,
    )
    negative_finding = Finding(
        strategy="Market Impact",
        conclusion="Negative impact on Nifty",
        evidence=[
            {
                "source_type": "market_reaction",
                "content": "",
                "metadata": {"asset": "Nifty", "percentage_change": -2.0},
            }
        ],
        confidence=0.6,
    )

    # Mock a strategy that returns these findings
    mock_strategy = AsyncMock()
    mock_strategy.analyze.return_value = [positive_finding, negative_finding]

    engine = ReasoningEngineService(strategies=[mock_strategy])

    # 2. Act
    result = await engine.reason(AnalyzedEvidence())

    # 3. Assert
    assert len(result.contradictions) == 1
    assert "Contradictory evidence found for asset 'Nifty'" in result.contradictions[0]


async def test_scenario_generation_service_builds_correct_prompt():
    """Verify the scenario generator calls the LLM with a well-formed prompt."""
    # 1. Arrange
    mock_llm = MagicMock()
    mock_llm.generate_text.return_value = "This is a bullish narrative."
    service = ScenarioGenerationService(llm_provider=mock_llm)

    positive_finding = Finding(
        strategy="Market Impact",
        conclusion="Suggests positive impact",
        evidence=[],
        confidence=0.8,
    )

    # 2. Act
    await service.generate_scenarios(findings=[positive_finding], contradictions=[])

    # 3. Assert
    # Check that the LLM was called to generate a bullish scenario
    bullish_call_args = mock_llm.generate_text.call_args_list[0]
    prompt = bullish_call_args[0][0]
    assert "write a coherent 'Bullish' scenario narrative" in prompt
    assert "Suggests positive impact" in prompt