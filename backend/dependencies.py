"""FastAPI dependency injectors for services and repositories."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_db_session
from backend.repositories.graph_repository import (
    EntityRepository,
    RelationshipRepository,
)
from backend.repositories.historical_repository import HistoricalRepository
from backend.repositories.statistics_repository import StatisticsRepository
from backend.repositories.timeline_repository import TimelineRepository
from backend.services.graph_service import (
    GraphBuilderService,
    EntityResolutionService,
    GraphAnalyticsService,
    GraphTraversalService,
    RelationshipExtractionService,
)
from backend.services.gemini_service import GeminiService
from backend.services.statistics_service import StatisticsService
from backend.services.timeline_service import TimelineService


def get_timeline_service(
    session: AsyncSession = Depends(get_db_session),
) -> TimelineService:
    """Inject a TimelineService instance."""
    historical_repo = HistoricalRepository(session)
    timeline_repo = TimelineRepository(session)
    return TimelineService(historical_repo, timeline_repo)


def get_statistics_service(
    session: AsyncSession = Depends(get_db_session),
) -> StatisticsService:
    """Inject a StatisticsService instance."""
    stats_repo = StatisticsRepository(session)
    return StatisticsService(stats_repo)


def get_entity_repository(
    session: AsyncSession = Depends(get_db_session),
) -> EntityRepository:
    """Inject an EntityRepository instance."""
    return EntityRepository(session)


def get_relationship_repository(
    session: AsyncSession = Depends(get_db_session),
) -> RelationshipRepository:
    """Inject a RelationshipRepository instance."""
    return RelationshipRepository(session)


def get_entity_resolution_service(
    entity_repo: EntityRepository = Depends(get_entity_repository),
) -> EntityResolutionService:
    """Inject an EntityResolutionService instance."""
    return EntityResolutionService(entity_repo)


def get_graph_traversal_service(
    relationship_repo: RelationshipRepository = Depends(
        get_relationship_repository
    ),
) -> GraphTraversalService:
    """Inject a GraphTraversalService instance."""
    return GraphTraversalService(relationship_repo)


def get_graph_analytics_service(
    entity_repo: EntityRepository = Depends(get_entity_repository),
    relationship_repo: RelationshipRepository = Depends(
        get_relationship_repository
    ),
) -> GraphAnalyticsService:
    """Inject a GraphAnalyticsService instance."""
    return GraphAnalyticsService(entity_repo, relationship_repo)


def get_gemini_service() -> GeminiService:
    """Inject a GeminiService instance."""
    return GeminiService()


def get_relationship_extraction_service(
    gemini_service: GeminiService = Depends(get_gemini_service),
) -> RelationshipExtractionService:
    """Inject a RelationshipExtractionService instance."""
    return RelationshipExtractionService(gemini_service)


def get_graph_builder_service(
    entity_resolution_service: EntityResolutionService = Depends(
        get_entity_resolution_service
    ),
    relationship_extraction_service: RelationshipExtractionService = Depends(
        get_relationship_extraction_service
    ),
    entity_repo: EntityRepository = Depends(get_entity_repository),
    relationship_repo: RelationshipRepository = Depends(
        get_relationship_repository
    ),
) -> GraphBuilderService:
    """Inject a GraphBuilderService instance."""
    return GraphBuilderService(
        entity_resolution_service,
        relationship_extraction_service,
        entity_repo,
        relationship_repo,
    )