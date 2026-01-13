"""
Data classes for entity query operations in the RBAC system.
"""

from __future__ import annotations

from dataclasses import dataclass

from .types import EntityType


@dataclass(frozen=True)
class EntityData:
    """Information about an entity within a scope."""

    entity_type: EntityType
    entity_id: str


@dataclass(frozen=True)
class EntityListResult:
    """Result of entity search with pagination info."""

    items: list[EntityData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
