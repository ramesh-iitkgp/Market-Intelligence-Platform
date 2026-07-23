"""SQLAlchemy models for the Knowledge Graph."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum as SqlEnum,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base for graph models."""


class EntityType(enum.Enum):
    """Enum for supported entity types in the graph."""

    COMPANY = "COMPANY"
    COUNTRY = "COUNTRY"
    GOVERNMENT = "GOVERNMENT"
    CENTRAL_BANK = "CENTRAL_BANK"
    SECTOR = "SECTOR"
    INDUSTRY = "INDUSTRY"
    INDEX = "INDEX"
    COMMODITY = "COMMODITY"
    CURRENCY = "CURRENCY"
    PERSON = "PERSON"
    HISTORICAL_EVENT = "HISTORICAL_EVENT"
    ORGANIZATION = "ORGANIZATION"
    # Add other types from the spec...


class RelationshipType(enum.Enum):
    """Enum for supported relationship types in the graph."""

    OWNS = "OWNS"
    SUBSIDIARY_OF = "SUBSIDIARY_OF"
    LOCATED_IN = "LOCATED_IN"
    AFFECTS = "AFFECTS"
    CAUSES = "CAUSES"
    RELATED_TO = "RELATED_TO"
    EVENT_CAUSED = "EVENT_CAUSED"
    # Add other types from the spec...


class EntityNode(Base):
    """Represents a node in the Knowledge Graph."""

    __tablename__ = "graph_entity_nodes"
    __table_args__ = (UniqueConstraint("canonical_name", "entity_type"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    entity_type: Mapped[EntityType] = mapped_column(SqlEnum(EntityType), index=True)
    canonical_name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    metadata: Mapped[dict | None] = mapped_column(JSONB)
    embedding_ref: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    aliases: Mapped[list[EntityAlias]] = relationship(
        "EntityAlias", back_populates="node", cascade="all, delete-orphan"
    )
    source_relationships: Mapped[list[RelationshipEdge]] = relationship(
        "RelationshipEdge",
        foreign_keys="[RelationshipEdge.source_node_id]",
        back_populates="source_node",
        cascade="all, delete-orphan",
    )
    target_relationships: Mapped[list[RelationshipEdge]] = relationship(
        "RelationshipEdge",
        foreign_keys="[RelationshipEdge.target_node_id]",
        back_populates="target_node",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<EntityNode(id={self.id}, name='{self.canonical_name}', type='{self.entity_type.name}')>"


class EntityAlias(Base):
    """Represents an alias for an entity node."""

    __tablename__ = "graph_entity_aliases"
    __table_args__ = (UniqueConstraint("alias", "node_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    alias: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    node_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("graph_entity_nodes.id"), nullable=False
    )

    node: Mapped[EntityNode] = relationship("EntityNode", back_populates="aliases")

    def __repr__(self) -> str:
        return f"<EntityAlias(alias='{self.alias}', node_id={self.node_id})>"


class RelationshipEdge(Base):
    """Represents a directed, typed relationship between two entity nodes."""

    __tablename__ = "graph_relationship_edges"
    __table_args__ = (
        UniqueConstraint("source_node_id", "target_node_id", "relationship_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_node_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("graph_entity_nodes.id"), index=True
    )
    target_node_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("graph_entity_nodes.id"), index=True
    )
    relationship_type: Mapped[RelationshipType] = mapped_column(
        SqlEnum(RelationshipType), index=True
    )

    confidence_score: Mapped[float | None] = mapped_column(Float)
    weight: Mapped[float | None] = mapped_column(Float, default=1.0)
    evidence: Mapped[str | None] = mapped_column(Text)
    provenance: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    source_node: Mapped[EntityNode] = relationship(
        "EntityNode",
        foreign_keys=[source_node_id],
        back_populates="source_relationships",
    )
    target_node: Mapped[EntityNode] = relationship(
        "EntityNode",
        foreign_keys=[target_node_id],
        back_populates="target_relationships",
    )

    def __repr__(self) -> str:
        return (
            f"<RelationshipEdge(source={self.source_node_id}, "
            f"target={self.target_node_id}, type='{self.relationship_type.name}')>"
        )

```

This set of models provides a robust and extensible foundation for the Knowledge Graph.

*   **UUIDs** are used for primary keys on nodes and edges, ensuring they can be generated independently before insertion.
*   **Enums** provide type safety and clarity for entity and relationship types.
*   **`JSONB`** is used for `metadata` and `provenance`, offering a flexible way to store rich, unstructured data.
*   **Relationships** are clearly defined with back-population, ensuring that the graph can be navigated efficiently in either direction from any node.
*   **Unique constraints** are in place to prevent duplicate nodes (by name and type) and duplicate relationships between the same two nodes.

With this schema foundation in place, the next logical step is to build the repository layer that will encapsulate all database interactions for these new models.

<!--
[PROMPT_SUGGESTION]Implement the `GraphRepository` and `EntityRepository` with methods for creating, retrieving, and searching for nodes and aliases.[/PROMPT_SUGGESTION]
[PROMPT_SUGGESTION]Create the `EntityResolutionService` that uses the new repositories to find or create canonical entity nodes from raw text.[/PROMPT_SUGGESTION]
-->