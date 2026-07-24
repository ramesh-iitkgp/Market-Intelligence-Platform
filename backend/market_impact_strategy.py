"""Reasoning strategy based on market impact analysis."""

from __future__ import annotations

from backend.schemas.reasoning_schemas import AnalyzedEvidence, EvidenceSource, Finding
from backend.services.reasoning.base import ReasoningStrategy


class MarketImpactStrategy(ReasoningStrategy):
    """
    Analyzes market reactions from similar events to infer potential impact.
    """

    @property
    def name(self) -> str:
        return "Market Impact"

    async def analyze(self, evidence: AnalyzedEvidence) -> list[Finding]:
        """
        Generates findings based on market reactions of similar events.

        Args:
            evidence: The structured evidence from the EvidenceAnalyzerService.

        Returns:
            A list of findings about potential market impact.
        """
        findings = []
        for reaction in evidence.market_reactions:
            conclusion = (
                f"Historical data suggests a potential impact on '{reaction.asset}'. "
                f"In a similar past event, it experienced a {reaction.percentage_change:.2f}% change over a {reaction.period} period."
            )

            finding_evidence = EvidenceSource(
                source_type="market_reaction",
                content=f"Asset '{reaction.asset}' changed by {reaction.percentage_change:.2f}%",
                metadata=reaction.model_dump(),
            )

            findings.append(
                Finding(
                    strategy=self.name,
                    conclusion=conclusion,
                    evidence=[finding_evidence],
                    confidence=0.7,  # Confidence can be refined
                    reasoning_chain=[
                        f"Identified historical market reaction for asset '{reaction.asset}'.",
                        f"Evidence showed a {reaction.percentage_change:.2f}% change over a {reaction.period} period.",
                        "Inferred a potential for similar market impact based on this historical reaction.",
                    ],
                )
            )
        return findings