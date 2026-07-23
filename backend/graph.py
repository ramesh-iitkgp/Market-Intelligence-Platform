"""API endpoints for the Knowledge Graph."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import (
    get_entity_repository,
    get_graph_builder_service,
    get_graph_analytics_service,
    get_graph_traversal_service,
    get_relationship_repository,
    get_timeline_service,
    get_db_session,
)
from backend.repositories.graph_repository import (
    EntityRepository,
    RelationshipRepository,
)
from backend.schemas.graph_schemas import (
    GraphBuildRequest,
    GraphBuildResponse,
    DegreeCentralityResponse,
    EntityNodeRead,
    NeighborsResponse,
)
from backend.services.graph_service import (
    GraphBuilderService,
    GraphAnalyticsService,
    GraphTraversalService,
)
from backend.services.timeline_service import TimelineService

router = APIRouter(prefix="/graph", tags=["Knowledge Graph"])


@router.get(
    "/entity/{node_id}",
    response_model=EntityNodeRead,
    summary="Get Entity Node by ID",
)
async def get_entity_by_id(
    node_id: uuid.UUID,
    entity_repo: EntityRepository = Depends(get_entity_repository),
):
    """
    Retrieve a single entity node from the graph by its unique ID.

    This endpoint provides the full details of an entity, including its canonical
    name, type, description, and all known aliases.

    - **Error Response:** Returns a `404 Not Found` if the UUID does not
      correspond to any entity in the graph.
    """
    node = await entity_repo.get_by_id(node_id)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity node with ID {node_id} not found.",
        )
    return node


@router.get(
    "/entity/search",
    response_model=list[EntityNodeRead],
    summary="Search for Entity Nodes",
)
async def search_entities(
    query: str = Query(
        ..., min_length=2, description="Search query for entity name or alias."
    ),
    limit: int = Query(10, gt=0, le=50, description="Maximum number of results."),
    entity_repo: EntityRepository = Depends(get_entity_repository),
):
    """
    Search for entity nodes by their canonical name or an alias.
    The search is case-insensitive.

    Example Usage:
    - `?query=Reserve Bank` will match "Reserve Bank of India".
    - `?query=rbi` will match the same entity via its alias.
    """
    nodes = await entity_repo.search_by_name_or_alias(query, limit=limit)
    return nodes


@router.get(
    "/neighbors/{node_id}",
    response_model=NeighborsResponse,
    summary="Get Neighbors of an Entity Node",
)
async def get_neighbors(
    node_id: uuid.UUID,
    entity_repo: EntityRepository = Depends(get_entity_repository),
    relationship_repo: RelationshipRepository = Depends(get_relationship_repository),
):
    """
    Retrieve a node and all its direct neighbors in the graph, regardless of
    the relationship direction.

    This is useful for exploring the immediate connections of a particular
    company, country, or event.
    """
    # First, get the primary node
    node = await entity_repo.get_by_id(node_id)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity node with ID {node_id} not found.",
        )

    # Then, get its neighbors
    neighbors = await relationship_repo.get_neighbors(node_id)

    return NeighborsResponse(node=node, neighbors=neighbors)


@router.get(
    "/path",
    response_model=list[EntityNodeRead],
    summary="Find Shortest Path Between Two Nodes",
)
async def find_shortest_path(
    start_node_id: uuid.UUID = Query(..., description="The starting node ID."),
    end_node_id: uuid.UUID = Query(..., description="The ending node ID."),
    max_depth: int = Query(5, gt=1, le=10, description="Maximum path depth."),
    traversal_service: GraphTraversalService = Depends(get_graph_traversal_service),
):
    """
    Finds the shortest path of connected entities between a start node and
    an end node.

    This powerful feature allows you to discover non-obvious, multi-hop
    relationships between two entities of interest. For example, how is a
    specific company connected to a geopolitical event?
    """
    path = await traversal_service.find_shortest_path(
        start_node_id, end_node_id, max_depth
    )
    if not path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No path found between {start_node_id} and {end_node_id} within {max_depth} hops.",
        )
    return path


@router.get(
    "/statistics/degree",
    response_model=list[DegreeCentralityResponse],
    summary="Get Top Nodes by Degree Centrality",
)
async def get_degree_centrality(
    limit: int = Query(10, gt=0, le=50, description="Number of nodes to return."),
    analytics_service: GraphAnalyticsService = Depends(
        get_graph_analytics_service
    ),
):
    """
    Calculates the degree centrality (total number of connections) for all nodes
    and returns the top N most connected nodes. This is useful for identifying
    the most influential or central entities in the knowledge graph.
    """
    top_nodes = await analytics_service.get_top_nodes_by_degree(limit)
    return top_nodes


@router.post(
    "/build",
    response_model=GraphBuildResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Build Graph from a Historical Event",
)
async def build_graph_from_event(
    request: GraphBuildRequest,
    builder_service: GraphBuilderService = Depends(get_graph_builder_service),
    timeline_service: TimelineService = Depends(get_timeline_service),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Triggers the process to extract entities and relationships from a single
    historical event and add them to the Knowledge Graph. This is an
    asynchronous-style endpoint that accepts the request and returns a `202 Accepted`
    status to indicate that processing has begun.

    **Note:** In a production environment, this operation would be handed off
    to a background task queue (e.g., Celery) to avoid blocking the API server.
    """
    event = await timeline_service.get_event_by_id(request.event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Historical event with ID {request.event_id} not found.",
        )

    # In a production system, this would likely be sent to a background worker (e.g., Celery).
    # For now, we process it directly but commit at the end.
    await builder_service.process_event(event)
    await session.commit()

    return GraphBuildResponse(
        status="processing_started",
        message="Graph build process initiated for the event.",
        event_id=request.event_id,
    )