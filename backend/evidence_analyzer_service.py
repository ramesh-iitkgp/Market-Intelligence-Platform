"""
Service for analyzing and structuring the evidence retrieved from the RAG engine.
"""

from __future__ import annotations

import logging

from backend.database.graph_models import EntityNode
from backend.database.historical_models import HistoricalEvent
from backend.schemas.rag_schemas import RAGContext, RetrievedItem, Source
from backend.schemas.reasoning_schemas import (
    AnalyzedEvidence,
    AnalyzedMarketReaction,
    AnalyzedSimilarEvent,
)


class EvidenceAnalyzerService:
    """
    Parses the raw RAGContext and transforms it into a structured AnalyzedEvidence model.

    This service acts as a bridge between the RAG retrieval phase and the reasoning
    phase. It simplifies the input for reasoning strategies by providing a clean,
    strongly-typed object to work with, rather than a heterogeneous list of items.
    """

    def __init__(self, logger: logging.Logger | None = None):
        self._logger = logger or logging.getLogger(__name__)

    def analyze(self, context: RAGContext) -> AnalyzedEvidence:
        """
        Transforms a RAGContext object into a structured AnalyzedEvidence object.

        Args:
            context: The raw context retrieved by the RAG engine.

        Returns:
            A structured and typed representation of the evidence.
        """
        self._logger.info("Analyzing RAG context to structure evidence.")
        analyzed_evidence = AnalyzedEvidence(query_event=context.query_event)

        for item in context.retrieved_items:
            self._process_retrieved_item(item, analyzed_evidence)

        # In the future, this service could also fetch external data like
        # economic indicators for the relevant period.

        return analyzed_evidence

    def _process_retrieved_item(
        self, item: RetrievedItem, analyzed_evidence: AnalyzedEvidence
    ) -> None:
        """Processes a single RetrievedItem and adds it to the structured evidence."""
        source = item.evidence.source

        if source == Source.SIMILARITY_ENGINE and isinstance(item.item, HistoricalEvent):
            similar_event = AnalyzedSimilarEvent(
                event=item.item,
                similarity_score=item.evidence.final_score,
                explanation=item.evidence.metadata.get("explanation", "N/A"),
            )
            analyzed_evidence.similar_events.append(similar_event)

        elif source == Source.GRAPH_NEIGHBORHOOD and isinstance(item.item, EntityNode):
            analyzed_evidence.key_entities.append(item.item)

        elif source == Source.TIMELINE_CONTEXT and isinstance(item.item, HistoricalEvent):
            analyzed_evidence.timeline_context.append(item.item)

        # Placeholder for market reaction analysis. This would be expanded when
        # a dedicated retrieval strategy for market reactions is implemented.
        elif source == Source.MARKET_REACTION and isinstance(item.item, dict):
            reaction = AnalyzedMarketReaction(**item.item)
            analyzed_evidence.market_reactions.append(reaction)