"""Similarity strategy based on shared entities and their types."""

from __future__ import annotations

from backend.database.graph_models import EntityNode, EntityType
from backend.database.historical_models import HistoricalEvent
from backend.repositories.graph_repository import EntityRepository
from backend.services.similarity.base import SimilarityStrategy


class EntitySimilarityStrategy(SimilarityStrategy):
    """
    Calculates similarity based on shared entities, weighted by entity type.

    This strategy improves upon a simple entity overlap by assigning more
    importance to shared entities of certain types (e.g., a shared Central Bank
    is more significant than a shared company).
    """

    def __init__(self, entity_repo: EntityRepository):
        self._entity_repo = entity_repo
        # These weights can be tuned or moved to a configuration file.
        self._entity_type_weights: dict[EntityType, float] = {
            EntityType.CENTRAL_BANK: 1.0,
            EntityType.GOVERNMENT: 0.9,
            EntityType.COUNTRY: 0.9,
            EntityType.HISTORICAL_EVENT: 0.8,
            EntityType.COMMODITY: 0.7,
            EntityType.CURRENCY: 0.6,
            EntityType.INDEX: 0.6,
            EntityType.SECTOR: 0.5,
            EntityType.INDUSTRY: 0.4,
            EntityType.COMPANY: 0.3,
            EntityType.PERSON: 0.2,
            EntityType.ORGANIZATION: 0.2,
        }

    @property
    def name(self) -> str:
        return "entity"

    async def calculate(
        self,
        query_event: HistoricalEvent,
        candidates: list[HistoricalEvent],
    ) -> list[tuple[int, float]]:
        query_nodes = await self._entity_repo.get_nodes_for_event(query_event.id)
        if not query_nodes:
            return []

        scores = []
        for candidate in candidates:
            if candidate.id == query_event.id:
                continue

            candidate_nodes = await self._entity_repo.get_nodes_for_event(candidate.id)
            score = self._weighted_jaccard_similarity(query_nodes, candidate_nodes)
            scores.append((candidate.id, score))

        return scores

    def _weighted_jaccard_similarity(
        self, set_a: list[EntityNode], set_b: list[EntityNode]
    ) -> float:
        """Calculates Jaccard similarity weighted by entity type importance."""
        map_a = {node.id: self._entity_type_weights.get(node.entity_type, 0.1) for node in set_a}
        map_b = {node.id: self._entity_type_weights.get(node.entity_type, 0.1) for node in set_b}

        intersection_keys = map_a.keys() & map_b.keys()
        union_keys = map_a.keys() | map_b.keys()

        intersection_weight = sum(min(map_a.get(k, 0), map_b.get(k, 0)) for k in intersection_keys)
        union_weight = sum(max(map_a.get(k, 0), map_b.get(k, 0)) for k in union_keys)

        return intersection_weight / union_weight if union_weight > 0 else 0.0