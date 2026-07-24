"""Similarity strategy based on Knowledge Graph structure."""

from __future__ import annotations

from backend.database.historical_models import HistoricalEvent
from backend.repositories.graph_repository import EntityRepository
from backend.services.similarity.base import SimilarityStrategy


class GraphSimilarityStrategy(SimilarityStrategy):
    """
    Calculates similarity based on the overlap of entities in the Knowledge Graph.

    This strategy measures how similar two events are by comparing the sets of
    entities (companies, countries, etc.) that are connected to each event in
    the graph.
    """

    def __init__(self, entity_repo: EntityRepository):
        self._entity_repo = entity_repo

    @property
    def name(self) -> str:
        return "graph"

    async def calculate(
        self,
        query_event: HistoricalEvent,
        candidates: list[HistoricalEvent],
    ) -> list[tuple[int, float]]:
        query_nodes = await self._entity_repo.get_nodes_for_event(query_event.id)
        query_node_ids = {node.id for node in query_nodes}

        if not query_node_ids:
            return []

        scores = []
        for candidate in candidates:
            if candidate.id == query_event.id:
                continue

            candidate_nodes = await self._entity_repo.get_nodes_for_event(candidate.id)
            candidate_node_ids = {node.id for node in candidate_nodes}

            intersection = len(query_node_ids.intersection(candidate_node_ids))
            union = len(query_node_ids.union(candidate_node_ids))

            jaccard_score = intersection / union if union > 0 else 0.0
            scores.append((candidate.id, jaccard_score))

        return scores