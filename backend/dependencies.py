"""FastAPI dependency injectors for services and repositories."""

from __future__ import annotations
from typing import Sequence

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_db_session
from backend.repositories.graph_repository import (
    EntityRepository,
    RelationshipRepository,
)
from backend.repositories.historical_repository import HistoricalRepository
from backend.repositories.embedding_repository import EmbeddingRepository
from backend.repositories.reaction_repository import ReactionRepository
from backend.repositories.statistics_repository import StatisticsRepository
from backend.repositories.timeline_repository import TimelineRepository
from backend.services.graph_service import (
    GraphBuilderService,
    EntityResolutionService,
    GraphAnalyticsService,
    GraphTraversalService,
    RelationshipExtractionService,
)
from backend.services.llm.base import LLMProvider
from backend.services.llm.gemini import GeminiProvider
from backend.services.statistics_service import StatisticsService
from backend.services.timeline_service import TimelineService
from backend.services.similarity.base import SimilarityStrategy
from backend.services.similarity.embedding_strategy import EmbeddingSimilarityStrategy
from backend.services.similarity.graph_strategy import GraphSimilarityStrategy
from backend.services.similarity.entity_strategy import EntitySimilarityStrategy
from backend.services.similarity.market_reaction_strategy import MarketReactionSimilarityStrategy
from backend.services.similarity.timeline_strategy import TimelineSimilarityStrategy
from backend.services.similarity_service import SimilarityEngineService
from backend.services.composite_similarity_service import CompositeSimilarityService
from backend.services.rag.assembly import ContextAssemblyService
from backend.services.rag.base import RetrievalStrategy
from backend.services.rag.ranking import RankingService
from backend.services.rag.retrieval import RetrievalService
from backend.services.rag.prompt_builder import PromptBuilderService
from backend.services.rag.strategies import SimilarityRetrievalStrategy, TimelineRetrievalStrategy, GraphNeighborhoodRetrievalStrategy
from backend.services.reasoning.evidence_analyzer_service import EvidenceAnalyzerService
from backend.services.reasoning.scenario_generation_service import (
    ScenarioGenerationService,
)
from backend.services.reasoning.strategies.historical_strategy import (
    HistoricalReasoningStrategy,
)
from backend.services.reasoning.strategies.market_impact_strategy import (
    MarketImpactStrategy,
)
from backend.services.reasoning.strategies.risk_strategy import RiskReasoningStrategy
from backend.services.reasoning.strategies.placeholder_strategies import (
    CompanyReasoningStrategy, MacroeconomicReasoningStrategy, PolicyReasoningStrategy, RiskReasoningStrategy, SectorReasoningStrategy
)
from backend.services.rag_service import RAGEngineService
from backend.services.reasoning.base import ReasoningStrategy
from backend.services.reasoning_service import FinancialReasoningService, ReasoningEngineService


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


def get_llm_provider() -> LLMProvider:
    """Inject a concrete LLMProvider instance based on configuration."""
    # This factory can be extended to support other providers.
    return GeminiProvider()


def get_relationship_extraction_service(
    llm_provider: LLMProvider = Depends(get_llm_provider),
) -> RelationshipExtractionService:
    """Inject a RelationshipExtractionService instance."""
    return RelationshipExtractionService(llm_provider)


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


def get_embedding_repository() -> EmbeddingRepository:
    """Inject an EmbeddingRepository instance."""
    # In a real application, this would likely be a singleton.
    return EmbeddingRepository()


def get_reaction_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ReactionRepository:
    """Inject a ReactionRepository instance."""
    return ReactionRepository(session)


def get_similarity_strategies(
    embedding_repo: EmbeddingRepository = Depends(get_embedding_repository),
    entity_repo: EntityRepository = Depends(get_entity_repository),
    reaction_repo: ReactionRepository = Depends(get_reaction_repository),
    timeline_repo: TimelineRepository = Depends(get_timeline_repository),
) -> list[SimilarityStrategy]:
    """Assemble and inject a list of all concrete similarity strategies."""
    return [
        EmbeddingSimilarityStrategy(embedding_repo),
        GraphSimilarityStrategy(entity_repo),
        EntitySimilarityStrategy(entity_repo),
        MarketReactionSimilarityStrategy(reaction_repo),
        TimelineSimilarityStrategy(timeline_repo),
    ]


def get_similarity_engine_service(
    strategies: list[SimilarityStrategy] = Depends(get_similarity_strategies),
    historical_repo: HistoricalRepository = Depends(get_timeline_service),
) -> SimilarityEngineService:
    """Inject a SimilarityEngineService instance."""
    # The historical_repo is available via the timeline_service's dependencies
    return SimilarityEngineService(
        strategies, historical_repo=historical_repo._historical_repo
    )


def get_composite_similarity_service(
    similarity_engine: SimilarityEngineService = Depends(
        get_similarity_engine_service
    ),
    historical_repo: HistoricalRepository = Depends(get_timeline_service),
) -> CompositeSimilarityService:
    """Inject a CompositeSimilarityService instance."""
    return CompositeSimilarityService(
        similarity_engine, historical_repo=historical_repo._historical_repo
    )


def get_rag_retrieval_strategies(
    composite_similarity_service: CompositeSimilarityService = Depends(get_composite_similarity_service),
    timeline_service: TimelineService = Depends(get_timeline_service),
    entity_repo: EntityRepository = Depends(get_entity_repository),
    relationship_repo: RelationshipRepository = Depends(get_relationship_repository),
) -> list[RetrievalStrategy]:
    """Assemble and inject all concrete RAG retrieval strategies."""
    return [
        SimilarityRetrievalStrategy(composite_similarity_service),
        TimelineRetrievalStrategy(timeline_service),
        GraphNeighborhoodRetrievalStrategy(entity_repo, relationship_repo),
    ]

def get_rag_retrieval_service(strategies: list[RetrievalStrategy] = Depends(get_rag_retrieval_strategies)) -> RetrievalService:
    """Inject a RAG RetrievalService instance."""
    return RetrievalService(strategies=strategies)


def get_rag_ranking_service() -> RankingService:
    """Inject a RAG RankingService instance."""
    return RankingService()


def get_rag_prompt_builder_service(
    llm_provider: LLMProvider = Depends(get_llm_provider),
) -> PromptBuilderService:
    """Inject a RAG PromptBuilderService instance."""
    # The prompt builder depends on the tokenizer from the configured LLM provider
    return PromptBuilderService(tokenizer=llm_provider.tokenizer)


def get_rag_engine_service(
    retrieval_service: RetrievalService = Depends(get_rag_retrieval_service),
    ranking_service: RankingService = Depends(get_rag_ranking_service),
    assembly_service: ContextAssemblyService = Depends(lambda: ContextAssemblyService()),
    prompt_builder_service: PromptBuilderService = Depends(get_rag_prompt_builder_service),
) -> RAGEngineService:
    """Inject the main RAGEngineService instance."""
    return RAGEngineService(
        retrieval_service, ranking_service, assembly_service, prompt_builder_service
    )


def get_reasoning_strategies() -> list[ReasoningStrategy]:
    """
    Assemble and inject all concrete financial reasoning strategies.    
    """
    return [
        HistoricalReasoningStrategy(),
        MarketImpactStrategy(),
        # RiskReasoningStrategy is now handled separately
        SectorReasoningStrategy(),
        CompanyReasoningStrategy(),
        MacroeconomicReasoningStrategy(),
        PolicyReasoningStrategy(),
    ]


def get_risk_reasoning_strategy() -> RiskReasoningStrategy:
    """Inject the concrete RiskReasoningStrategy."""
    return RiskReasoningStrategy()


def get_evidence_analyzer_service() -> EvidenceAnalyzerService:
    """Inject an EvidenceAnalyzerService instance."""
    return EvidenceAnalyzerService()


def get_reasoning_engine_service(
    strategies: list[ReasoningStrategy] = Depends(get_reasoning_strategies),
) -> ReasoningEngineService:
    """Inject a ReasoningEngineService instance."""
    return ReasoningEngineService(strategies=strategies)


def get_scenario_generation_service(
    llm_provider: LLMProvider = Depends(get_llm_provider),
) -> ScenarioGenerationService:
    """Inject a ScenarioGenerationService instance."""
    return ScenarioGenerationService(llm_provider)


def get_financial_reasoning_service(
    rag_engine: RAGEngineService = Depends(get_rag_engine_service),
    evidence_analyzer: EvidenceAnalyzerService = Depends(
        get_evidence_analyzer_service
    ),
    reasoning_engine: ReasoningEngineService = Depends(get_reasoning_engine_service),
    risk_strategy: RiskReasoningStrategy = Depends(get_risk_reasoning_strategy),
    scenario_generator: ScenarioGenerationService = Depends(
        get_scenario_generation_service
    ),
) -> FinancialReasoningService:
    """Inject the main FinancialReasoningService instance."""
    return FinancialReasoningService(
        rag_engine, evidence_analyzer, reasoning_engine, risk_strategy, scenario_generator
    )