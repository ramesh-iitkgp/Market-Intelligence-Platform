# Market Intelligence Platform - Architecture

This document provides a comprehensive overview of the software architecture for the Market Intelligence Platform. It is intended for developers, architects, and technical stakeholders.

## 1. Project Overview

The Market Intelligence Platform is an AI-powered system designed to transform historical events, live news, and market data into explainable decision support for global markets. It ingests unstructured and structured data, builds a rich semantic understanding through a Knowledge Graph, and uses this intelligence to find historical parallels, analyze market reactions, and generate context for advanced reasoning.

## 2. High-Level Architecture

The platform is built on a modular, multi-layered architecture where each component has a distinct responsibility. Data flows from ingestion through various stages of processing and enrichment, ultimately being exposed via a REST API.

```text
External Data Sources (News APIs, Market Data)
           |
           v
[Phase 1: Data Collection & Normalization]
           |
           v
+------------------------------------------------+
|               Source of Truth                  |
|    [PostgreSQL - Relational Database]          |
|     - Historical Events                        |
|     - Market Reactions                         |
|     - Raw Articles                             |
+------------------------------------------------+
           |
           v
+------------------------------------------------+
|             Semantic Intelligence              |
| [Phase 3.5: AI-Powered Knowledge Graph]        |
|  - Entities (Nodes)                            |
|  - Relationships (Edges)                       |
|  - Built by GraphBuilderService via LLM        |
+------------------------------------------------+
           |
           v
+------------------------------------------------+
|          Historical Intelligence               |
| [Phase 4: Similarity Engine]                   |
|  - Hybrid Scoring (Vector, Graph, Timeline)    |
|  - Composite Ranking                           |
|  - Explainable AI                              |
+------------------------------------------------+
           |
           v
+------------------------------------------------+
|          Context Generation Layer              |
| [Phase 5: RAG Context Builder]                 |
|  - Retrieve -> Rank -> Assemble Pipeline       |
|  - Token-Aware Prompt Generation               |
+------------------------------------------------+
           |
           v
[FastAPI - REST API Layer]
           |
           v
Downstream Consumers (Clients, Reasoning Engines)
```

## 3. Folder Structure

The project is organized into a clean, feature-oriented structure.

```
backend/
├── api/              # FastAPI routers and API-level logic
├── core/             # Core components (exceptions, logging)
├── database/         # SQLAlchemy models and migrations
├── repositories/     # Data access layer (isolates DB logic)
├── schemas/          # Pydantic models for API contracts
├── services/         # Business logic and service orchestration
└── tests/            # Unit, integration, and API tests
```

## 4. Technology Stack

*   **Backend Framework**: FastAPI
*   **Database**: PostgreSQL
*   **ORM**: SQLAlchemy 2.x (Async)
*   **Data Validation**: Pydantic V2
*   **AI/LLM**: Google Gemini (via `google-genai` SDK)
*   **Vector Embeddings**: Sentence-Transformers (with abstractions for FAISS, pgvector, etc.)
*   **Testing**: Pytest, Testcontainers, `pytest-xdist`, `factory-boy`
*   **Code Quality**: Ruff, Black, isort, mypy, pre-commit

## 5. Design Principles

*   **Clean Architecture**: The codebase is strictly divided into layers (API, Service, Repository) to separate concerns.
*   **SOLID Principles**: The design emphasizes single responsibility, dependency inversion, and interface segregation.
*   **Dependency Injection (DI)**: FastAPI's `Depends` system is used extensively to manage dependencies, making components modular and testable.
*   **Repository Pattern**: All database access is encapsulated within repository classes, decoupling business logic from data persistence details.
*   **Strategy Pattern**: Complex, multi-faceted logic (like similarity scoring and RAG retrieval) is built using the Strategy pattern, promoting extensibility and modularity.
*   **Async Everywhere**: The entire backend stack, from the API down to the database, is asynchronous to ensure high throughput.

## 6. Clean Architecture Layers

1.  **API Layer (`backend/api/`)**: Contains FastAPI routers. Its sole responsibility is to handle HTTP requests, validate inputs using Pydantic, call the appropriate service, and serialize the response. It contains no business logic.
2.  **Service Layer (`backend/services/`)**: Contains the core business logic of the application. Services orchestrate calls to one or more repositories to fulfill a use case. Examples include `CompositeSimilarityService` and `RAGEngineService`.
3.  **Repository Layer (`backend/repositories/`)**: Contains all data access logic. Each repository is responsible for a specific domain (e.g., `HistoricalRepository`, `GraphRepository`) and encapsulates all SQLAlchemy queries. This is the only layer that directly interacts with the database.

## 7. Database Schema Overview

The platform uses a relational PostgreSQL database with two primary schemas:

*   **Historical Schema (`historical_models.py`)**: This is the source of truth for factual event data.
    *   `historical_events`: Stores discrete events with details like title, description, date, importance, and category.
    *   `historical_reactions`: Stores the quantitative market reaction (e.g., price change) for specific assets linked to an event.
    *   `event_entities`: A mapping table linking events to the entities involved.

*   **Graph Schema (`graph_models.py`)**: This schema stores the semantic layer.
    *   `graph_entity_nodes`: Represents canonical entities (e.g., "Reserve Bank of India").
    *   `graph_entity_aliases`: Stores alternative names for entities (e.g., "RBI").
    *   `graph_relationship_edges`: Represents the directed, typed relationships between entities (e.g., `(RBI) -[REGULATES]-> (India)`).

## 8. Knowledge Graph Architecture

The Knowledge Graph provides the semantic understanding of how entities are related.

*   **Construction**: The `GraphBuilderService` orchestrates graph creation.
    1.  It uses the `RelationshipExtractionService` (powered by an LLM like Gemini) to analyze unstructured text from a `HistoricalEvent`.
    2.  The LLM returns a structured JSON object containing detected entities and relationships.
    3.  The `EntityResolutionService` takes the extracted entity names and resolves them to canonical `EntityNode` objects, creating new nodes or matching existing ones via aliases.
    4.  Finally, `RelationshipEdge` objects are created to link the resolved nodes in the database.
*   **Querying**: The `GraphRepository` and `RelationshipRepository` provide methods for graph traversal (`get_neighbors`, `find_shortest_path`) and analytics (`calculate_degree_centrality`).

## 9. Historical Similarity Engine

The Similarity Engine (Phase 4) is designed to find historical parallels using a hybrid approach, orchestrated by the `CompositeSimilarityService`. It uses a **Strategy Pattern** to combine scores from multiple independent strategies:

*   `EmbeddingSimilarityStrategy`: Calculates cosine similarity on text embeddings.
*   `GraphSimilarityStrategy`: Uses Jaccard similarity on the sets of graph nodes connected to each event.
*   `EntitySimilarityStrategy`: A weighted Jaccard similarity that gives more importance to shared entities like central banks or governments.
*   `MarketReactionSimilarityStrategy`: Compares the quantitative market impact of events.
*   `TimelineSimilarityStrategy`: Compares the sequence of preceding events to find similar contexts.

The `CompositeSimilarityService` takes the scores from each strategy, applies configurable weights, and produces a single, ranked list of the most similar events, complete with an explanation.

## 10. RAG Context Builder

The RAG Context Builder (Phase 5) is an intelligent middleware layer that prepares evidence for downstream reasoning. It operates as a three-stage pipeline, orchestrated by the `RAGEngineService`:

1.  **Retrieve**: The `RetrievalService` uses multiple, parallel `RetrievalStrategy` classes to gather evidence from all available sources:
    *   `SimilarityRetrievalStrategy`: Fetches top similar events.
    *   `GraphNeighborhoodRetrievalStrategy`: Fetches connected entities from the Knowledge Graph.
    *   `TimelineRetrievalStrategy`: Fetches preceding and succeeding events.
2.  **Rank**: The `RankingService` takes all retrieved items, applies a weighted score based on the source's reliability, and deduplicates the list to keep only the most relevant information.
3.  **Assemble**: The `ContextAssemblyService` organizes the ranked evidence into a structured `RAGContext` Pydantic model.

Finally, the `PromptBuilderService` converts this structured context into a token-aware, LLM-ready prompt string, complete with citations and diagnostic information.

## 11. Financial Reasoning Engine

The Financial Reasoning Engine (Phase 6) is the primary intelligence layer of the platform. It consumes the `RAGContext` and performs a multi-pass analysis to generate evidence-based narratives, scenarios, and risk assessments.

### Workflow

1.  **Evidence Analysis**: The `EvidenceAnalyzerService` transforms the raw `RAGContext` into a strongly-typed `AnalyzedEvidence` model, separating similar events, graph entities, market reactions, etc.
2.  **Primary Reasoning**: The `ReasoningEngineService` executes multiple `ReasoningStrategy` classes in parallel (e.g., `HistoricalReasoningStrategy`, `MarketImpactStrategy`).
3.  **Synthesis**: The engine then synthesizes the findings from all strategies to identify `contradictions` (e.g., conflicting market impact data) and `uncertainties` (e.g., missing evidence).
4.  **Risk Analysis**: A dedicated `RiskReasoningStrategy` runs as a second pass. It analyzes the initial findings, contradictions, and uncertainties to generate a specific list of categorized risks.
5.  **Scenario Generation**: Finally, the `ScenarioGenerationService` uses an LLM to synthesize the findings into coherent bullish, bearish, and base-case narratives. It is strictly instructed to use only the provided findings as evidence, ensuring no hallucination.

### Explainability

Every `Finding` produced by the engine includes:
*   A list of `EvidenceSource` objects, linking it directly to the data from the RAG context.
*   A `reasoning_chain`, which is a human-readable log of the logical steps the strategy took to form its conclusion.

## 11. API Structure

The API is built with FastAPI and follows RESTful principles. Endpoints are organized into versioned routers based on functionality.

*   `/api/v1/historical`: For searching and retrieving historical events.
*   `/api/v1/graph`: For querying the Knowledge Graph (nodes, neighbors, paths).
*   `/api/v1/similarity`: For accessing the Historical Similarity Engine.
*   `/api/v1/rag`: For accessing the RAG Context Builder.
*   `/api/v1/reasoning`: For accessing the Financial Reasoning Engine.

All request and response bodies are strictly validated using Pydantic models defined in the `schemas/` directory.

## 12. Repository Layer

The repository layer (`repositories/`) is the cornerstone of our data access strategy.

*   **Purpose**: To completely isolate the application's business logic from the specifics of data storage.
*   **Implementation**: Each repository class (e.g., `HistoricalRepository`) takes an `AsyncSession` in its constructor and exposes methods that perform specific database operations (e.g., `search`, `get_by_id`).
*   **Benefit**: This allows us to change the database or ORM with minimal impact on the service layer. It also makes services highly testable, as repositories can be easily mocked.

## 13. Service Layer

The service layer (`services/`) contains all the business logic.

*   **Purpose**: To orchestrate data and operations to fulfill a specific use case.
*   **Implementation**: Services depend on repositories or other services, which are provided via dependency injection. They are stateless and process data passed to them.
*   **Example**: The `CompositeSimilarityService` depends on the `SimilarityEngineService` and `HistoricalRepository`. It calls the engine to get scores, then calls the repository to get full event details before assembling the final result.

## 14. Dependency Injection

We leverage FastAPI's built-in dependency injection system (`Depends`) extensively.

*   **File**: `backend/dependencies.py`
*   **Purpose**: This file contains provider functions that are responsible for instantiating and wiring together all services and repositories.
*   **Example**: The `get_composite_similarity_service` provider function first depends on `get_similarity_engine_service`, which in turn depends on `get_similarity_strategies`, and so on. FastAPI resolves this dependency graph for each incoming request, providing the API endpoint with the fully constructed service it needs.

## 15. Request Flow Example (`POST /rag/context`)

1.  An HTTP request hits the `/rag/context` endpoint in `api/v1/rag.py`.
2.  FastAPI validates the incoming JSON against the `RAGQuery` Pydantic model.
3.  FastAPI's dependency injector calls `get_rag_engine_service`. This triggers a chain of calls in `dependencies.py` to construct the entire RAG service stack, including all retrieval strategies.
4.  The API handler calls `rag_engine.generate_context(request)`.
5.  The `RAGEngineService` orchestrates the `Retrieve -> Rank -> Assemble` pipeline by calling the respective services.
6.  The `RetrievalService` runs all its strategies concurrently (`asyncio.gather`).
7.  The final `RAGContext` object is returned to the API handler.
8.  FastAPI serializes the Pydantic model into a JSON response and sends it to the client.

## 16. Background Jobs

For long-running, resource-intensive tasks, the architecture is designed to accommodate a background job queue like **Celery**.

*   **Use Cases**:
    *   **Graph Building**: The `POST /graph/build` endpoint is designed to be asynchronous. In production, instead of processing the event directly, it would dispatch a task to a Celery worker.
    *   **Embedding Generation**: Calculating vector embeddings for new historical events is another ideal candidate for background processing.
*   **Benefit**: This prevents long-running tasks from blocking the API server, ensuring the application remains responsive.

## 17. Configuration

Application configuration is managed via `.env` files and loaded into a Pydantic `Settings` object. This provides type-safe, validated, and environment-aware configuration. Key settings include database connection strings, log levels, and the `GEMINI_API_KEY`.

## 18. Testing Strategy

The project employs a comprehensive, multi-layered testing strategy to ensure quality and reliability.

*   **Unit Tests**: Located in `tests/unit/`, these tests are fast and isolated. They test individual services and components by mocking their dependencies (e.g., testing `RankingService` logic without a database).
*   **Integration Tests**: Located in `tests/integration/`, these tests validate the interaction between components. They use **Testcontainers** to programmatically spin up a real PostgreSQL database for each test session. Alembic migrations are run to ensure the test schema matches production exactly. Each test runs in an isolated transaction that is rolled back, guaranteeing no side effects.
*   **Test Data**: `factory-boy` is used to generate deterministic test data, eliminating flaky tests and boilerplate setup.
*   **Code Quality**: `pre-commit` hooks are configured to automatically run `ruff`, `black`, `isort`, and `mypy` before every commit, enforcing a consistent code style.
*   **CI/CD**: The CI pipeline (e.g., GitHub Actions) is configured to run all quality checks, unit tests, and integration tests on every pull request. Coverage is enforced, and the build will fail if it drops below the configured threshold (e.g., 90%).

## 19. Security Considerations

*   **Secrets Management**: API keys and other secrets are managed via `.env` files and are never committed to version control.
*   **Input Validation**: All API inputs are strictly validated by Pydantic, preventing common injection and data-type-related vulnerabilities.
*   **Dependency Security**: The project should use tools like `pip-audit` or GitHub's Dependabot to scan for vulnerabilities in third-party packages.
*   **Authentication**: While not yet implemented, the API layer is where authentication and authorization (e.g., using OAuth2) would be added to protect sensitive endpoints.

## 20. Performance Optimizations

*   **Asynchronous Operations**: The entire stack is async, from the database driver (`asyncpg`) to the ORM (SQLAlchemy 2.x) and the web framework (FastAPI).
*   **Efficient Data Loading**: Repositories use `selectinload` instead of `joinedload` for loading related collections to avoid the N+1 query problem and reduce memory usage.
*   **Parallelism**: Services like `RetrievalService` use `asyncio.gather` to run I/O-bound operations concurrently.
*   **Indexing**: Database tables have appropriate indexes on foreign keys and frequently queried columns to ensure fast lookups.
*   **Caching**: The architecture is ready for a caching layer (e.g., Redis) to be added for frequently accessed, expensive operations like similarity searches or graph traversals.

## 21. Project Roadmap

### Completed Phases

*   **✅ Phase 1**: Data Collection & Normalization
*   **✅ Phase 2**: Knowledge Repository (SQL Schema)
*   **✅ Phase 3**: Historical Event Database & Timeline Engine
*   **✅ Phase 3.1**: Engineering Quality & Test Infrastructure
*   **✅ Phase 3.5**: AI-Powered Knowledge Graph
*   **✅ Phase 4**: Historical Similarity & Historical Intelligence Engine
*   **✅ Phase 5**: RAG Context Builder & Production Hardening

### Upcoming Phases

*   **Phase 6**: Financial Reasoning Engine (Consumes RAG context to generate analytical narratives).
*   **Phase 7**: Explainable Decision Support System (Provides a user-facing interface with full traceability).
*   **Phase 8**: Operationalization (Monitoring, alerting, deployment automation).