"""
Data classes for entity query operations in the RBAC system.
"""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.manager.data.common.types import SearchResult

from .association_scopes_entities import AssociationScopesEntitiesData
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


@dataclass(frozen=True)
class EntityRefListResult(SearchResult[AssociationScopesEntitiesData]):
    """Result of entity ref search with full association row data."""

    pass
