"""Concrete retrieval strategies for the RAG engine."""

from __future__ import annotations

from backend.database.graph_models import EntityNode, RelationshipType
from backend.database.historical_models import HistoricalEvent
from backend.repositories.graph_repository import EntityRepository, RelationshipRepository
from backend.schemas.rag_schemas import Evidence, RAGQuery, RetrievedItem, Source
from backend.services.composite_similarity_service import CompositeSimilarityService
from backend.services.rag.base import RetrievalStrategy
from backend.services.timeline_service import TimelineService


class SimilarityRetrievalStrategy(RetrievalStrategy):
    """Retrieves historically similar events."""

    def __init__(self, composite_service: CompositeSimilarityService):
        self._composite_service = composite_service

    async def retrieve(self, query: RAGQuery) -> list[RetrievedItem]:
        """Find similar events using the composite similarity service."""
        if not query.query_event:
            return []

        similar_events_result = await self._composite_service.find_and_rank_similar_events(
            query.query_event, top_k=query.top_k
        )

        items = []
        for result in similar_events_result:
            evidence = Evidence(
                source=Source.SIMILARITY_ENGINE,
                score=result.score.overall,
                content=result.event.description,
                metadata={
                    "event_id": result.event.id,
                    "event_title": result.event.title,
                    "explanation": result.explanation.reason,
                },
            )
            items.append(RetrievedItem(evidence=evidence, item=result.event))
        return items


class GraphNeighborhoodRetrievalStrategy(RetrievalStrategy):
    """Retrieves the graph neighborhood for entities in the query event."""

    def __init__(
        self,
        entity_repo: EntityRepository,
        relationship_repo: RelationshipRepository,
        max_neighbors: int = 10,
    ):
        self._entity_repo = entity_repo
        self._relationship_repo = relationship_repo
        self._max_neighbors = max_neighbors
        # Configurable weights for different relationship types.
        self._relationship_weights: dict[RelationshipType, float] = {
            RelationshipType.OWNS: 1.0,
            RelationshipType.SUBSIDIARY_OF: 1.0,
            RelationshipType.CAUSES: 0.9,
            RelationshipType.EVENT_CAUSED: 0.9,
            RelationshipType.AFFECTS: 0.8,
            RelationshipType.LOCATED_IN: 0.5,
            RelationshipType.RELATED_TO: 0.3,
        }

    async def retrieve(self, query: RAGQuery) -> list[RetrievedItem]:
        """Find direct neighbors for all entities involved in the query event."""
        if not query.query_event or not query.query_event.entities:
            return []

        # 1. Resolve all entities from the historical event to graph nodes
        source_nodes: list[EntityNode] = []
        for event_entity in query.query_event.entities:
            # This assumes a mapping from historical entity type to graph entity type exists.
            # For this example, we'll assume the types are compatible.
            try:
                node = await self._entity_repo.find_by_name(
                    name=event_entity.entity.name, entity_type=event_entity.entity.type.upper()
                )
                if node:
                    source_nodes.append(node)
            except ValueError:
                # Gracefully handle cases where the entity type is not in the graph enum
                continue

        if not source_nodes:
            return []

        # 2. Fetch all neighbor edges and calculate scores
        scored_neighbors: dict[str, tuple[EntityNode, float]] = {}
        for source_node in source_nodes:
            edges = await self._relationship_repo.get_neighbor_edges(source_node.id)
            for edge in edges:
                neighbor_node = edge.target_node if edge.source_node_id == source_node.id else edge.source_node
                if neighbor_node.id == source_node.id:
                    continue

                # Calculate score
                type_weight = self._relationship_weights.get(edge.relationship_type, 0.2)
                confidence = edge.confidence_score or 0.5
                score = type_weight * confidence

                # Keep the neighbor with the highest score if seen before
                if neighbor_node.id not in scored_neighbors or score > scored_neighbors[neighbor_node.id][1]:
                    scored_neighbors[neighbor_node.id] = (neighbor_node, score)

        # 3. Sort by score and format as RetrievedItems
        sorted_neighbors = sorted(scored_neighbors.values(), key=lambda x: x[1], reverse=True)

        items = []
        for neighbor, score in sorted_neighbors[:self._max_neighbors]:
            evidence = Evidence(
                source=Source.GRAPH_NEIGHBORHOOD,
                score=score,
                content=f"This entity is connected to the primary event. Canonical Name: {neighbor.canonical_name}",
                metadata={
                    "node_id": str(neighbor.id),
                    "node_type": neighbor.entity_type.value,
                },
            )
            items.append(RetrievedItem(evidence=evidence, item=neighbor))
        return items


class TimelineRetrievalStrategy(RetrievalStrategy):
    """Retrieves events that occurred immediately before and after the query event."""

    def __init__(self, timeline_service: TimelineService, window: int = 3):
        self._timeline_service = timeline_service
        self._window = window

    async def retrieve(self, query: RAGQuery) -> list[RetrievedItem]:
        """Get surrounding events from the timeline."""
        if not query.query_event:
            return []

        prev_events, _, next_events = await self._timeline_service.get_timeline_around_event(
            query.query_event.id, window=self._window
        )

        items = []
        for event in prev_events:
            items.append(self._create_retrieved_item(event, "preceding_event"))

        for event in next_events:
            items.append(self._create_retrieved_item(event, "following_event"))

        return items

    def _create_retrieved_item(
        self, event: HistoricalEvent, context: str
    ) -> RetrievedItem:
        """Helper to create a RetrievedItem from a HistoricalEvent."""
        evidence = Evidence(
            source=Source.TIMELINE_CONTEXT,
            score=0.8,  # High score as it's direct temporal context
            content=event.description,
            metadata={
                "event_id": event.id,
                "event_title": event.title,
                "context": context,
            },
        )
        return RetrievedItem(evidence=evidence, item=event)