"""Unit tests for concrete reasoning strategies."""

from __future__ import annotations

import pytest

from backend.schemas.reasoning_schemas import (
    AnalyzedEvidence,
    AnalyzedMarketReaction,
    AnalyzedSimilarEvent,
    ReasoningResult,
)
from backend.services.reasoning.strategies.historical_strategy import (
    HistoricalReasoningStrategy,
)
from backend.services.reasoning.strategies.market_impact_strategy import (
    MarketImpactStrategy,
)
from backend.services.reasoning.strategies.risk_strategy import RiskReasoningStrategy
from tests.factories.historical import HistoricalEventFactory

pytestmark = pytest.mark.asyncio


async def test_historical_reasoning_strategy():
    """Verify the HistoricalReasoningStrategy generates correct findings."""
    strategy = HistoricalReasoningStrategy()
    evidence = AnalyzedEvidence(
        similar_events=[
            AnalyzedSimilarEvent(
                event=HistoricalEventFactory.build(title="Test Event"),
                similarity_score=0.85,
                explanation="Similar text",
            )
        ]
    )

    findings = await strategy.analyze(evidence)

    assert len(findings) == 1
    assert findings[0].strategy == "Historical Parallels"
    assert "Test Event" in findings[0].conclusion
    assert findings[0].confidence == 0.85
    assert len(findings[0].reasoning_chain) == 3


async def test_market_impact_strategy():
    """Verify the MarketImpactStrategy generates correct findings."""
    strategy = MarketImpactStrategy()
    evidence = AnalyzedEvidence(
        market_reactions=[
            AnalyzedMarketReaction(asset="USD/INR", percentage_change=2.1, period="5D")
        ]
    )

    findings = await strategy.analyze(evidence)

    assert len(findings) == 1
    assert findings[0].strategy == "Market Impact"
    assert "USD/INR" in findings[0].conclusion
    assert "2.10%" in findings[0].conclusion


async def test_risk_reasoning_strategy():
    """Verify the RiskReasoningStrategy identifies risks from initial results."""
    strategy = RiskReasoningStrategy()
    evidence = AnalyzedEvidence()
    initial_result = ReasoningResult(
        uncertainties=["No strong historical parallels were found."],
        contradictions=["Contradictory evidence found for asset 'Gold'."],
    )

    findings = await strategy.analyze(evidence, initial_result=initial_result)

    assert len(findings) == 2
    assert any("Uncertainty Risk" in f.conclusion for f in findings)
    assert any("Contradiction Risk" in f.conclusion for f in findings)
    assert all(f.strategy == "Risk Identification" for f in findings)