"""
Data classes for entity query operations in the RBAC system.
"""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.manager.data.common.types import SearchResult

from .types import EntityType


@dataclass(frozen=True)
class EntityData:
    """Information about an entity within a scope."""

    entity_type: EntityType
    entity_id: str


@dataclass(frozen=True)
class EntityListResult(SearchResult[EntityData]):
    """Result of entity search with pagination info."""

    pass
