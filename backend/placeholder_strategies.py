"""Placeholder implementations for future reasoning strategies."""

from __future__ import annotations

from backend.schemas.reasoning_schemas import AnalyzedEvidence, Finding
from backend.services.reasoning.base import ReasoningStrategy


class SectorReasoningStrategy(ReasoningStrategy):
    @property
    def name(self) -> str:
        return "Sector Analysis"

    async def analyze(self, evidence: AnalyzedEvidence) -> list[Finding]:
        return []


class CompanyReasoningStrategy(ReasoningStrategy):
    @property
    def name(self) -> str:
        return "Company Analysis"

    async def analyze(self, evidence: AnalyzedEvidence) -> list[Finding]:
        return []


class MacroeconomicReasoningStrategy(ReasoningStrategy):
    @property
    def name(self) -> str:
        return "Macroeconomic Context"

    async def analyze(self, evidence: AnalyzedEvidence) -> list[Finding]:
        return []


class RiskReasoningStrategy(ReasoningStrategy):
    @property
    def name(self) -> str:
        return "Risk Identification"

    async def analyze(self, evidence: AnalyzedEvidence) -> list[Finding]:
        return []


class PolicyReasoningStrategy(ReasoningStrategy):
    @property
    def name(self) -> str:
        return "Policy & Regulation"

    async def analyze(self, evidence: AnalyzedEvidence) -> list[Finding]:
        return []