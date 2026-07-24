"""Repositories for accessing and manipulating the Knowledge Graph."""

from __future__ import annotations
import json

import uuid
from typing import Sequence

from sqlalchemy import and_, func, or_, select, union_all
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.graph_models import (
    EntityAlias,
    EntityNode,
    EntityType,
    RelationshipEdge,
)


class EntityRepository:
    """Provides data access for entity nodes and their aliases."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository with an async database session."""
        self._session = session

    async def add(self, node: EntityNode) -> None:
        """Add a single entity node to the session."""
        self._session.add(node)

    async def get_by_id(self, node_id: uuid.UUID) -> EntityNode | None:
        """Retrieve an entity node by its UUID, with its aliases."""
        stmt = (
            select(EntityNode)
            .options(selectinload(EntityNode.aliases))
            .where(EntityNode.id == node_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_ids(self, node_ids: list[uuid.UUID]) -> Sequence[EntityNode]:
        """Retrieve multiple entity nodes by their UUIDs."""
        if not node_ids:
            return []
        stmt = (
            select(EntityNode).options(selectinload(EntityNode.aliases)).where(EntityNode.id.in_(node_ids))
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def find_by_name(
        self, name: str, entity_type: EntityType
    ) -> EntityNode | None:
        """Find an entity node by its canonical name and type."""
        stmt = select(EntityNode).where(
            EntityNode.canonical_name == name, EntityNode.entity_type == entity_type
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_alias(self, alias_text: str) -> EntityNode | None:
        """Find an entity node by one of its aliases."""
        stmt = (
            select(EntityNode)
            .join(EntityAlias)
            .options(selectinload(EntityNode.aliases))
            .where(EntityAlias.alias == alias_text)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def search_by_name_or_alias(
        self, query: str, limit: int = 10
    ) -> Sequence[EntityNode]:
        """Search for entity nodes by name or alias, case-insensitively."""
        # This query finds nodes where either the canonical name or any alias matches
        stmt = (
            select(EntityNode)
            .outerjoin(EntityAlias)
            .where(
                or_(
                    EntityNode.canonical_name.ilike(f"%{query}%"),
                    EntityAlias.alias.ilike(f"%{query}%"),
                )
            )
            .distinct()
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_nodes_for_event(self, event_id: int) -> Sequence[EntityNode]:
        """
        Retrieve all entity nodes connected to a specific historical event.

        This works by finding relationship edges where the event ID is stored
        in the provenance metadata.
        """
        # This query finds all nodes that are either a source or a target
        # in a relationship originating from the given event.
        stmt = (
            select(EntityNode)
            .join(RelationshipEdge, or_(EntityNode.id == RelationshipEdge.source_node_id, EntityNode.id == RelationshipEdge.target_node_id))
            .where(RelationshipEdge.provenance["event_id"].astext == str(event_id))
            .distinct()
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_neighbor_edges(self, node_id: uuid.UUID) -> Sequence[RelationshipEdge]:
        """Retrieve all relationship edges connected to a given node."""
        stmt = (
            select(RelationshipEdge)
            .options(
                selectinload(RelationshipEdge.source_node),
                selectinload(RelationshipEdge.target_node),
            )
            .where(
                or_(
                    RelationshipEdge.source_node_id == node_id,
                    RelationshipEdge.target_node_id == node_id,
                )
            )
        )
        result = await self._session.execute(stmt)
        return result.scalars().unique().all()


class RelationshipRepository:
    """Provides data access for relationship edges in the graph."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository with an async database session."""
        self._session = session

    async def add(self, edge: RelationshipEdge) -> None:
        """Add a single relationship edge to the session."""
        self._session.add(edge)

    async def get_neighbors(self, node_id: uuid.UUID) -> Sequence[EntityNode]:
        """Retrieve all direct neighbors of a given node."""
        # Find nodes where the given node is the source
        source_stmt = select(RelationshipEdge.target_node_id).where(
            RelationshipEdge.source_node_id == node_id
        )
        # Find nodes where the given node is the target
        target_stmt = select(RelationshipEdge.source_node_id).where(
            RelationshipEdge.target_node_id == node_id
        )

        neighbor_ids = (await self._session.execute(source_stmt.union(target_stmt))).scalars().all()

        if not neighbor_ids:
            return []

        # Fetch the full node objects for the neighbors
        nodes_stmt = select(EntityNode).where(EntityNode.id.in_(neighbor_ids))
        result = await self._session.execute(nodes_stmt)
        return result.scalars().all()

    async def find_shortest_path(
        self, start_node_id: uuid.UUID, end_node_id: uuid.UUID, max_depth: int = 5
    ) -> Sequence[EntityNode]:
        """
        Find the shortest path between two nodes using a bidirectional breadth-first search.

        This is implemented using a recursive CTE in PostgreSQL.
        """
        # CTE for traversing the graph
        path_cte = (
            select(
                RelationshipEdge.source_node_id.label("start_node"),
                RelationshipEdge.target_node_id.label("end_node"),
                [RelationshipEdge.source_node_id, RelationshipEdge.target_node_id].label("path"),
            )
            .where(RelationshipEdge.source_node_id == start_node_id)
            .cte("path_cte", recursive=True)
        )

        # Recursive part of the CTE
        path_cte = path_cte.union_all(
            select(
                path_cte.c.start_node,
                RelationshipEdge.target_node_id,
                path_cte.c.path + [RelationshipEdge.target_node_id],
            ).where(path_cte.c.end_node == RelationshipEdge.source_node_id)
        )

        # Final query to get the shortest path
        stmt = select(path_cte.c.path).where(path_cte.c.end_node == end_node_id).order_by(func.array_length(path_cte.c.path, 1)).limit(1)

        result = await self._session.execute(stmt)
        path_ids = result.scalar_one_or_none()

        if not path_ids:
            return []

        # Preserve the order from the path
        return await self._session.execute(select(EntityNode).where(EntityNode.id.in_(path_ids)).order_by(func.array_position(path_ids, EntityNode.id)))

    async def calculate_degree_centrality(
        self, limit: int = 10
    ) -> Sequence[tuple[uuid.UUID, int]]:
        """
        Calculate the degree centrality (total number of connections) for nodes.

        Returns a list of tuples containing (node_id, degree), ordered by degree.
        """
        source_nodes = select(RelationshipEdge.source_node_id.label("node_id"))
        target_nodes = select(RelationshipEdge.target_node_id.label("node_id"))

        all_connections = union_all(source_nodes, target_nodes).alias("all_connections")

        stmt = (
            select(
                all_connections.c.node_id,
                func.count(all_connections.c.node_id).label("degree"),
            )
            .group_by(all_connections.c.node_id)
            .order_by(func.count(all_connections.c.node_id).desc())
            .limit(limit)
        )

        result = await self._session.execute(stmt)
        return result.all()

```

This implementation provides the foundational data access patterns for the Knowledge Graph:

*   **`EntityRepository`** handles the creation and retrieval of nodes. It includes methods to find nodes by their canonical name or by any of their aliases, which is crucial for the upcoming `EntityResolutionService`.
*   **`RelationshipRepository`** is responsible for managing the edges. The initial `get_neighbors` method demonstrates a core graph traversal capability, finding all nodes connected to a given node, regardless of the direction of the relationship.

With this repository layer in place, we are now ready to build the service layer, starting with the `EntityResolutionService` which will use these repositories to intelligently map raw text to canonical nodes in our graph.

<!--
[PROMPT_SUGGESTION]Implement the `EntityResolutionService` that uses the `EntityRepository` to find or create canonical entity nodes.[/PROMPT_SUGGESTION]
[PROMPT_SUGGESTION]Create the Pydantic schemas and FastAPI endpoints for searching and retrieving graph entities.[/PROMPT_SUGGESTION]
-->