"""Service for generating plausible future scenarios from reasoned findings."""

from __future__ import annotations

import logging

from backend.schemas.reasoning_schemas import Finding, Scenario, ScenarioAnalysis
from backend.services.llm.base import LLMProvider


class ScenarioGenerationService:
    """
    Uses an LLM to synthesize findings into bullish, bearish, and neutral scenarios.

    This service takes the structured output from the ReasoningEngineService and
    constructs coherent, evidence-backed narratives for potential future outcomes.
    """

    def __init__(self, llm_provider: LLMProvider, logger: logging.Logger | None = None):
        self._llm_provider = llm_provider
        self._logger = logger or logging.getLogger(__name__)

    async def generate_scenarios(
        self, findings: list[Finding], contradictions: list[str]
    ) -> ScenarioAnalysis:
        """
        Generates bullish, bearish, and base-case scenarios.

        Args:
            findings: A list of all evidence-backed findings.
            contradictions: A list of detected contradictions.

        Returns:
            A ScenarioAnalysis object containing the generated scenarios.
        """
        self._logger.info("Generating financial scenarios from %d findings.", len(findings))

        # Separate findings into positive and negative indicators
        positive_findings = [f for f in findings if self._is_positive(f)]
        negative_findings = [f for f in findings if self._is_negative(f)]

        # Generate each scenario
        bullish_scenario = self._generate_single_scenario(
            "Bullish", positive_findings, negative_findings, contradictions
        )
        bearish_scenario = self._generate_single_scenario(
            "Bearish", negative_findings, positive_findings, contradictions
        )
        base_case_scenario = self._generate_single_scenario(
            "Base Case", findings, [], contradictions
        )

        return ScenarioAnalysis(
            bullish=bullish_scenario,
            bearish=bearish_scenario,
            base_case=base_case_scenario,
        )

    def _generate_single_scenario(
        self,
        scenario_type: str,
        primary_findings: list[Finding],
        counter_findings: list[Finding],
        contradictions: list[str],
    ) -> Scenario | None:
        """Generates one specific scenario using the LLM."""
        if not primary_findings:
            return None

        prompt = self._build_scenario_prompt(
            scenario_type, primary_findings, counter_findings, contradictions
        )
        narrative = self._llm_provider.generate_text(prompt, temperature=0.3)

        # Refined confidence calculation: weighted average of finding confidences
        total_primary_weight = sum(f.confidence for f in primary_findings)
        total_counter_weight = sum(f.confidence for f in counter_findings)
        total_weight = total_primary_weight + total_counter_weight
        if total_weight == 0:
            confidence = 0.5  # Neutral confidence if no weighted findings
        else:
            confidence = total_primary_weight / total_weight

        return Scenario(
            scenario_type=scenario_type,
            narrative=narrative,
            supporting_findings=primary_findings,
            confidence=confidence,
        )

    def _build_scenario_prompt(
        self,
        scenario_type: str,
        primary_findings: list[Finding],
        counter_findings: list[Finding],
        contradictions: list[str],
    ) -> str:
        """Constructs a detailed prompt for the LLM to generate a scenario narrative."""
        prompt = f"You are a financial analyst. Based ONLY on the evidence provided, write a coherent '{scenario_type}' scenario narrative.\n\n"
        prompt += "## Supporting Evidence:\n"
        for f in primary_findings:
            prompt += f"- {f.conclusion}\n"

        if counter_findings:
            prompt += "\n## Countervailing Evidence (to acknowledge):\n"
            for f in counter_findings:
                prompt += f"- {f.conclusion}\n"

        if contradictions:
            prompt += "\n## Key Contradictions to Consider:\n"
            for c in contradictions:
                prompt += f"- {c}\n"

        prompt += f"\n## Task:\nSynthesize the 'Supporting Evidence' into a single, plausible '{scenario_type}' narrative. Acknowledge the countervailing evidence and contradictions where appropriate. Do not introduce outside information."
        return prompt

    def _is_positive(self, finding: Finding) -> bool:
        """Heuristic to determine if a finding is positive."""
        if finding.strategy == "Market Impact":
            change = finding.evidence[0].metadata.get("percentage_change", 0)
            return change > 0
        # Default to neutral
        return False

    def _is_negative(self, finding: Finding) -> bool:
        """Heuristic to determine if a finding is negative."""
        if finding.strategy == "Market Impact":
            change = finding.evidence[0].metadata.get("percentage_change", 0)
            return change < 0
        # Default to neutral
        return False