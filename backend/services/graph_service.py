"""Service layer for Knowledge Graph operations."""

from __future__ import annotations

import itertools
import logging
from typing import Any

from pydantic import ValidationError
from backend.database.graph_models import (
    EntityAlias,
    EntityNode,
    EntityType,
    RelationshipEdge,
    RelationshipType,
)
from backend.database.historical_models import HistoricalEvent
from backend.repositories.graph_repository import (
    EntityRepository,
    RelationshipRepository,
)
from backend.schemas.ai_schemas import GraphExtractionResult
from backend.services.gemini_service import GeminiService

class EntityResolutionService:
    """
    Handles the logic of mapping raw entity mentions to canonical nodes.

    This service ensures that different names for the same entity (e.g., "RBI",
    "Reserve Bank of India") resolve to a single node in the graph.
    """

    def __init__(self, entity_repo: EntityRepository, logger: logging.Logger | None = None):
        """Initialize the service with an entity repository."""
        self._entity_repo = entity_repo
        self._logger = logger or logging.getLogger(__name__)

    async def find_or_create_node(
        self, name: str, entity_type: EntityType, aliases: list[str] | None = None
    ) -> EntityNode:
        """
        Find an existing entity node by name or alias, or create a new one.

        This is the core entity resolution logic. It checks for the entity
        under its primary name and all provided aliases. If found, it returns
        the existing node. If not, it creates a new canonical node.

        Args:
            name: The primary or canonical name for the entity.
            entity_type: The type of the entity.
            aliases: A list of alternative names for the entity.

        Returns:
            The existing or newly created EntityNode.
        """
        # 1. Normalize all potential names
        canonical_name = self._normalize_name(name)
        all_aliases = {self._normalize_name(a) for a in aliases} if aliases else set()
        search_terms = {canonical_name} | all_aliases

        # 2. Search for an existing node using any of the names
        for term in sorted(list(search_terms)):  # Sort for deterministic search
            # First, check if the term matches a canonical name
            node = await self._entity_repo.find_by_name(term, entity_type)
            if node:
                # Found a match, potentially add new aliases later
                return node

            # If not, check if it's a known alias
            node = await self._entity_repo.find_by_alias(term)
            if node and node.entity_type == entity_type:
                return node

        # 3. If no node was found, create a new one
        new_node = EntityNode(canonical_name=canonical_name, entity_type=entity_type)
        for alias_text in all_aliases:
            if alias_text != canonical_name:
                new_node.aliases.append(EntityAlias(alias=alias_text))
        await self._entity_repo.add(new_node)
        return new_node

    def _normalize_name(self, name: str) -> str:
        """Applies standard normalization to an entity name."""
        # More robust normalization to handle real-world aliases
        name = name.strip().lower()
        # Remove common punctuation
        name = name.replace(".", "").replace(",", "")
        # Remove common corporate suffixes
        suffixes = [" ltd", " inc", " limited", " corporation"]
        for suffix in suffixes:
            if name.endswith(suffix):
                name = name[: -len(suffix)]
        # Normalize whitespace
        return " ".join(name.split())


class RelationshipExtractionService:
    """
    Extracts semantic relationships between entities mentioned in text.

    In a real-world scenario, this service would use advanced NLP models,
    potentially leveraging the GeminiService, to understand the context and
    identify specific relationships (e.g., 'acquires', 'competes_with').
    """

    def __init__(
        self,
        gemini_service: GeminiService,
        logger: logging.Logger | None = None,
    ):
        """Initialize the service."""
        self._gemini_service = gemini_service
        self._logger = logger or logging.getLogger(__name__)

    async def extract_graph_from_text(
        self, text: str
    ) -> GraphExtractionResult | None:
        """
        Analyzes text to extract entities and their semantic relationships.

        This method uses a powerful LLM with a carefully engineered prompt and
        a strict JSON schema to produce structured, validated output.

        Args:
            text: The input text from a historical event or news article.

        Returns:
            A validated Pydantic model containing the extracted graph data,
            or None if extraction fails or produces no valid data.
        """
        prompt = self._build_prompt(text)
        schema = GraphExtractionResult.model_json_schema()

        try:
            response_json = self._gemini_service.generate_json(
                prompt, schema=schema, temperature=0.0
            )
            validated_result = GraphExtractionResult.model_validate(response_json)
            self._logger.info(
                "Successfully extracted %d entities and %d relationships.",
                len(validated_result.entities),
                len(validated_result.relationships),
            )
            return validated_result
        except ValidationError as e:
            self._logger.error("LLM response failed validation: %s", e)
            return None
        except Exception as e:
            self._logger.error("An unexpected error occurred during graph extraction: %s", e)
            return None

    def _build_prompt(self, text: str) -> str:
        """Constructs the detailed prompt for the LLM."""
        entity_types = ", ".join([e.value for e in EntityType])
        relationship_types = ", ".join([r.value for r in RelationshipType])

        return f"""
        Analyze the following financial or economic text. Your task is to act as a
        financial intelligence analyst and build a knowledge graph by extracting
        entities and their relationships.

        **Instructions:**
        1.  **Identify Entities:** Extract all relevant entities from the text.
            -   Valid Entity Types: {entity_types}
            -   Normalize entity names to their canonical form (e.g., "Fed" -> "Federal Reserve").
        2.  **Identify Relationships:** Identify directed relationships between the
            entities you found.
            -   Valid Relationship Types: {relationship_types}
            -   A relationship must be explicitly supported by a phrase or sentence in the text.
        3.  **Provide Evidence:** For each relationship, quote the exact sentence or
            phrase from the text that serves as evidence.
        4.  **Assign Confidence:** For each relationship, provide a confidence score
            from 0.0 to 1.0, where 1.0 means you are certain.
        5.  **Format Output:** Return your findings as a single, valid JSON object
            that strictly adheres to the provided schema. Do not include entities
            that have no relationships. Do not hallucinate information not present
            in the text.

        **Text to Analyze:**
        ---
        {text}
        ---
        """


class GraphBuilderService:
    """Orchestrates the construction of the Knowledge Graph from historical events."""

    def __init__(
        self,
        entity_resolution_service: EntityResolutionService,
        relationship_extraction_service: RelationshipExtractionService,
        entity_repo: EntityRepository,
        relationship_repo: RelationshipRepository,
        logger: logging.Logger | None = None,
    ):
        """Initialize the service with its dependencies."""
        self._entity_resolver = entity_resolution_service
        self._relationship_extractor = relationship_extraction_service
        self._entity_repo = entity_repo
        self._relationship_repo = relationship_repo
        self._logger = logger or logging.getLogger(__name__)

    async def process_event(self, event: HistoricalEvent) -> None:
        """
        Process a single historical event to update the knowledge graph.
        """
        self._logger.info("Processing event %d for graph construction.", event.id)

        # 1. Use the new AI service to extract a structured graph from the event's text
        extraction_result = await self._relationship_extractor.extract_graph_from_text(
            event.description
        )

        if not extraction_result or not extraction_result.entities:
            self._logger.warning("No graph data extracted for event %d.", event.id)
            return

        # 2. Resolve all extracted entities to canonical graph nodes
        resolved_nodes: dict[str, EntityNode] = {}
        for extracted_entity in extraction_result.entities:
            node = await self._entity_resolver.find_or_create_node(
                name=extracted_entity.name, entity_type=extracted_entity.type
            )
            # Store resolved nodes by their extracted name for easy lookup
            resolved_nodes[self._entity_resolver._normalize_name(extracted_entity.name)] = node

        # 3. Create the relationship edges using the resolved nodes
        created_count = 0
        for rel in extraction_result.relationships:
            source_name = self._entity_resolver._normalize_name(rel.source)
            target_name = self._entity_resolver._normalize_name(rel.target)

            source_node = resolved_nodes.get(source_name)
            target_node = resolved_nodes.get(target_name)

            if not source_node or not target_node:
                self._logger.warning(
                    "Skipping relationship due to unresolved node: %s -> %s",
                    rel.source,
                    rel.target,
                )
                continue

            edge = RelationshipEdge(
                source_node_id=source_node.id,
                target_node_id=target_node.id,
                relationship_type=rel.type,
                confidence_score=rel.confidence,
                evidence=rel.evidence,
                provenance={"source": "llm_extraction", "event_id": event.id},
            )
            await self._relationship_repo.add(edge)
            created_count += 1

        self._logger.info(
            "Created %d relationships for event %d.", created_count, event.id
        )


class GraphTraversalService:
    """Provides graph traversal algorithms."""

    def __init__(self, relationship_repo: RelationshipRepository):
        """Initialize the service with a relationship repository."""
        self._relationship_repo = relationship_repo

    async def find_shortest_path(
        self, start_node_id: uuid.UUID, end_node_id: uuid.UUID, max_depth: int = 5
    ) -> Sequence[EntityNode]:
        """
        Find the shortest path between two nodes.

        Args:
            start_node_id: The UUID of the starting node.
            end_node_id: The UUID of the ending node.
            max_depth: The maximum number of hops to traverse.

        Returns:
            A sequence of EntityNode objects representing the path, or an empty list if no path is found.
        """
        return await self._relationship_repo.find_shortest_path(
            start_node_id, end_node_id, max_depth
        )


class GraphAnalyticsService:
    """Provides graph analytics and metric calculations."""

    def __init__(
        self,
        entity_repo: EntityRepository,
        relationship_repo: RelationshipRepository,
    ):
        """Initialize the service with required repositories."""
        self._entity_repo = entity_repo
        self._relationship_repo = relationship_repo

    async def get_top_nodes_by_degree(
        self, limit: int = 10
    ) -> list[dict[str, EntityNode | int]]:
        """
        Get the most connected nodes based on degree centrality.
        """
        # 1. Get top nodes by degree from the repository
        centrality_results = await self._relationship_repo.calculate_degree_centrality(
            limit
        )
        if not centrality_results:
            return []

        # 2. Extract IDs and fetch all node objects in a single query to avoid N+1
        node_ids = [result[0] for result in centrality_results]
        nodes = await self._entity_repo.get_by_ids(node_ids)
        nodes_by_id = {node.id: node for node in nodes}

        # 3. Combine the results
        results = []
        for node_id, degree in centrality_results:
            if node := nodes_by_id.get(node_id):
                results.append({"node": node, "degree": degree})
        return results