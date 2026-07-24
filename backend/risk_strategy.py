"""Reasoning strategy for identifying and categorizing risks."""

from __future__ import annotations

from backend.schemas.reasoning_schemas import (
    AnalyzedEvidence,
    EvidenceSource,
    Finding,
    ReasoningResult,
)
from backend.services.reasoning.base import ReasoningStrategy


class RiskReasoningStrategy(ReasoningStrategy):
    """
    Analyzes the evidence and initial findings to identify potential risks.

    This strategy looks for negative indicators, conflicting evidence, and
    gaps in the data to formulate risk-related findings.
    """

    @property
    def name(self) -> str:
        return "Risk Identification"

    async def analyze(
        self, evidence: AnalyzedEvidence, initial_result: ReasoningResult | None = None
    ) -> list[Finding]:
        """
        Generates findings related to various categories of risk.

        Args:
            evidence: The structured evidence from the EvidenceAnalyzerService.
            initial_result: The result from the primary reasoning pass.

        Returns:
            A list of findings, each detailing a specific identified risk.
        """
        findings = []

        # 1. Risk from negative market reactions
        negative_reactions = [
            r for r in evidence.market_reactions if r.percentage_change < 0
        ]
        if negative_reactions:
            for reaction in negative_reactions:
                conclusion = f"Market Risk: Historical data shows a precedent for negative market impact on '{reaction.asset}', which previously saw a {reaction.percentage_change:.2f}% decline."
                findings.append(
                    Finding(
                        strategy=self.name,
                        conclusion=conclusion,
                        evidence=[
                            EvidenceSource(
                                source_type="market_reaction",
                                content=f"Asset '{reaction.asset}' changed by {reaction.percentage_change:.2f}%",
                                metadata=reaction.model_dump(),
                            )
                        ],
                        confidence=0.8,
                        reasoning_chain=[
                            f"Identified a historical negative market reaction for '{reaction.asset}'.",
                            f"The asset previously declined by {reaction.percentage_change:.2f}%.",
                            "Flagged this as a 'Market Risk' due to the negative precedent.",
                        ],
                    )
                )

        # 2. Risk from weak or missing evidence (using initial results)
        if initial_result:
            for uncertainty in initial_result.uncertainties:
                conclusion = f"Uncertainty Risk: {uncertainty}"
                findings.append(
                    Finding(
                        strategy=self.name,
                        conclusion=conclusion,
                        evidence=[],
                        confidence=0.6,
                        reasoning_chain=[
                            "The Composite Reasoning Engine detected a gap in the available evidence.",
                            f"Specifically: '{uncertainty}'.",
                            "Flagged this as an 'Uncertainty Risk' as it limits the analysis.",
                        ],
                    )
                )

            for contradiction in initial_result.contradictions:
                conclusion = f"Contradiction Risk: {contradiction}"
                findings.append(
                    Finding(
                        strategy=self.name,
                        conclusion=conclusion,
                        evidence=[],
                        confidence=0.7,
                        reasoning_chain=[
                            "The Composite Reasoning Engine detected conflicting findings.",
                            f"Specifically: '{contradiction}'.",
                            "Flagged this as a 'Contradiction Risk' due to the unpredictable nature of conflicting evidence.",
                        ],
                    )
                )

        return findings