"""API endpoints for the Financial Reasoning Engine."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.schemas.reasoning_schemas import ReasoningQuery, ReasoningResult
from backend.services.reasoning_service import FinancialReasoningService
from backend.dependencies import get_financial_reasoning_service

router = APIRouter(prefix="/reasoning", tags=["Reasoning Engine"])


@router.post(
    "/analyze",
    response_model=ReasoningResult,
    summary="Perform a full financial reasoning analysis",
    status_code=status.HTTP_200_OK,
)
async def analyze_event(
    query: ReasoningQuery,
    reasoning_service: FinancialReasoningService = Depends(get_financial_reasoning_service),
) -> ReasoningResult:
    """
    This endpoint orchestrates the full reasoning pipeline.

    - Takes a `ReasoningQuery` (event ID or text).
    - Retrieves context using the RAG engine.
    - Analyzes the evidence.
    - Runs multiple reasoning strategies to generate findings.
    - Synthesizes results to find contradictions and uncertainties.
    - Performs a dedicated risk analysis.
    - Generates bullish, bearish, and base-case scenarios.

    Returns a comprehensive, evidence-backed reasoning result.
    """
    try:
        result = await reasoning_service.generate_reasoning(query)
        return result
    except Exception as e:
        # In a production system, we would have more specific exception handling
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during reasoning: {e}",
        )


# Placeholder endpoints as per Milestone 8. The /analyze endpoint already provides
# the data for scenarios, risks, and explanations. These can be implemented
# if a more focused response is desired.

@router.post("/scenarios", summary="[Placeholder] Generate scenarios for an event")
async def get_scenarios(query: ReasoningQuery):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)

@router.post("/risks", summary="[Placeholder] Analyze risks for an event")
async def get_risks(query: ReasoningQuery):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)

@router.post("/explain", summary="[Placeholder] Explain a specific conclusion")
async def explain_conclusion(query: ReasoningQuery):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)

@router.get("/statistics", summary="[Placeholder] Get reasoning engine statistics")
async def get_statistics():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)