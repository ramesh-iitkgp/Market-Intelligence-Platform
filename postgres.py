"""
Fixtures for PostgreSQL integration testing.

These fixtures use Testcontainers to programmatically manage a real PostgreSQL
database. Each test function runs in an isolated, nested transaction that is
rolled back, ensuring full test isolation.
"""

from __future__ import annotations

from typing import AsyncGenerator

from alembic import command
from alembic.config import Config
import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.postgres import PostgresContainer

from backend.database.historical_models import Base


@pytest.fixture(scope="session")
def postgres_container() -> PostgresContainer:
    """Session-scoped fixture to start and stop a PostgreSQL container."""
    with PostgresContainer("postgres:16-alpine") as container:
        yield container


@pytest.fixture(scope="session")
async def pg_engine(postgres_container: PostgresContainer):
    """
    Creates a session-scoped PostgreSQL engine, runs Alembic migrations,
    and yields the engine.
    """
    conn_url = postgres_container.get_connection_url("asyncpg")
    engine = create_async_engine(conn_url)

    # Run Alembic migrations
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", postgres_container.get_connection_url())
    command.upgrade(alembic_cfg, "head")

    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def integration_db_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Yields a session that is part of a nested transaction, rolling back to a
    savepoint after the test.
    """
    async with pg_engine.connect() as connection:
        async with connection.begin() as transaction:
            Session = async_sessionmaker(bind=connection)
            async with Session() as session:
                yield session