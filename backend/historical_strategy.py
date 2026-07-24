"""Reasoning strategy based on historical parallels."""

from __future__ import annotations

from backend.schemas.reasoning_schemas import AnalyzedEvidence, EvidenceSource, Finding
from backend.services.reasoning.base import ReasoningStrategy


class HistoricalReasoningStrategy(ReasoningStrategy):
    """
    Analyzes similar historical events to draw parallels and suggest potential outcomes.
    """

    @property
    def name(self) -> str:
        return "Historical Parallels"

    async def analyze(self, evidence: AnalyzedEvidence) -> list[Finding]:
        """
        Generates findings based on historically similar events.

        Args:
            evidence: The structured evidence from the EvidenceAnalyzerService.

        Returns:
            A list of findings drawing parallels to past events.
        """
        findings = []
        for similar_event in evidence.similar_events:
            conclusion = (
                f"A historical parallel, '{similar_event.event.title}', suggests a potential for similar market dynamics. "
                f"This past event was deemed similar with a score of {similar_event.similarity_score:.2f}."
            )

            finding_evidence = EvidenceSource(
                source_type="historical_event",
                content=f"Event: {similar_event.event.title}\nDate: {similar_event.event.occurred_at.date()}\n"
                f"Summary: {similar_event.event.description}",
                score=similar_event.similarity_score,
                metadata={
                    "event_id": similar_event.event.id,
                    "similarity_explanation": similar_event.explanation,
                },
            )

            findings.append(
                Finding(
                    strategy=self.name,
                    conclusion=conclusion,
                    evidence=[finding_evidence],
                    confidence=similar_event.similarity_score,
                    reasoning_chain=[
                        f"Analyzed historical parallel: '{similar_event.event.title}' (Similarity: {similar_event.similarity_score:.2f}).",
                        f"Similarity based on: {similar_event.explanation}.",
                        "Inferred that similar market dynamics could occur based on this historical precedent.",
                    ],
                )
            )
        return findings