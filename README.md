# Market Intelligence Platform

## Project Vision

Market Intelligence Platform turns historical events, live news, and market data
into explainable decision support for global markets. The platform is being built
as a modular system: data is collected and normalized first, analytical and AI
services enrich it next, and API and Android clients present traceable insights.

## Architecture

```text
Data sources -> data_pipeline -> database / knowledge graph
                                      |
                               backend services
                         (AI, retrieval, analytics)
                                      |
                           FastAPI API -> Android client
```

The backend follows layered architecture. API handlers coordinate requests;
services implement use cases; repositories isolate persistence; schemas define
boundaries; and `core` and `config` provide shared operational concerns.

### Repository Architecture
```text
Raw Article -> Collector -> AI Extraction -> Validation -> Normalization -> DB Storage
 (Source)       (Fetch)       (Gemini)       (Pydantic)      (Taxonomy)     (PostgreSQL)
                                                                 |
                                                          Embedding Service
                                                          (Sentence-T)
```

## Folder Structure

```text
backend/        FastAPI-facing backend and application services
database/       Database schema, migrations, and local development assets
data_pipeline/  Market, news, and event ingestion workflows
datasets/       Versioned or documented source datasets
models/         Trained model artifacts and model metadata
research/       Research notes and market-analysis methodology
experiments/    Reproducible model and feature experiments
notebooks/      Exploratory analysis notebooks
android/        Native Android application
docs/           Architecture decisions, roadmap, and operational documentation
scripts/        Development and automation scripts
tests/          Cross-component test suite
tools/          Developer tooling and utilities
```

## Setup

This foundation targets Python 3.12.

```bash
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # only when creating a new local environment
```

Set `GEMINI_API_KEY` in `.env`; secrets are intentionally excluded from Git.
Optional configuration includes `GEMINI_MODEL` (defaults to
`gemini-2.5-flash`), `GEMINI_TIMEOUT_SECONDS`, `LOG_LEVEL`, `LOG_DIRECTORY`,
`ENVIRONMENT`, and `DEBUG`.

Run the quality checks and Gemini connectivity test:

```bash
black .
ruff check . --fix # or `ruff .` for just checking
pytest
python backend/test_gemini.py
```

### Running the Pipeline

```bash
black .
ruff check .
pytest
python backend/test_gemini.py
```

## Roadmap

To add a new data source, implement the `BaseCollector` interface and add it to the `run_pipeline.py` script. The pipeline will automatically handle the processing, extraction, and storage of the data.

---

1. Foundation: configuration, observability, AI service boundary, and quality tooling.
2. Data layer: market/news ingestion, normalized event storage, and provenance.
3. Intelligence layer: entity resolution, knowledge graph, event similarity, and retrieval.
4. Product layer: FastAPI endpoints, authentication, dashboards, and Android workflows.
5. Operations: monitoring, evaluation, access controls, deployment, and global scaling.

## Current Status

Phase 1 is active. The backend package includes environment-backed settings,
timestamped rotating logs, reusable domain errors, and a testable Gemini service
implemented with the current `google-genai` SDK.
