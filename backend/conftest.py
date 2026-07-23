"""
Global pytest configuration and root fixtures.

This file is intentionally kept lightweight. Most fixtures are defined
in the `tests.fixtures` module and are auto-imported by pytest.
"""
import factory
import pytest
import random
from faker import Faker

# Discovers and registers fixtures from the `fixtures` directory.
pytest_plugins = [
    "tests.fixtures.database",
    "tests.fixtures.events",
    "tests.fixtures.postgres",
    "tests.fixtures.repositories",
]


@pytest.fixture(scope="session", autouse=True)
def seed_random_generators():
    """Seed random number generators for deterministic test data."""
    random.seed(12345)
    Faker.seed(0)
    factory.random.reseed_random(12345)