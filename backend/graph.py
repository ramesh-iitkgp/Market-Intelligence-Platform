"""Factories for creating graph-related models for testing."""

from __future__ import annotations

import factory
from factory.alchemy import SQLAlchemyModelFactory

from backend.database.graph_models import (
    EntityNode,
    EntityType,
    RelationshipEdge,
    RelationshipType,
)


class EntityNodeFactory(SQLAlchemyModelFactory):
    """Factory for creating EntityNode instances."""

    class Meta:
        model = EntityNode
        sqlalchemy_session_persistence = "commit"

    entity_type = EntityType.COMPANY
    canonical_name = factory.Faker("company")


class RelationshipEdgeFactory(SQLAlchemyModelFactory):
    """Factory for creating RelationshipEdge instances."""

    class Meta:
        model = RelationshipEdge
        sqlalchemy_session_persistence = "commit"

    relationship_type = RelationshipType.RELATED_TO