from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ai.backend.common.data.permission.types import (
    GLOBAL_SCOPE_ID,
    EntityType,
    OperationType,
    RoleSource,
    ScopeType,
)

from .id import ScopeId

if TYPE_CHECKING:
    from ai.backend.manager.repositories.base import BatchQuerier

# Re-export types for easier access
__all__ = (
    "GLOBAL_SCOPE_ID",
    "EntityType",
    "OperationType",
    "RoleSource",
    "ScopeData",
    "ScopeListResult",
    "ScopeType",
    "SearchEntitiesParam",
)


@dataclass(frozen=True)
class ScopeData:
    """Data for a scope."""

    id: ScopeId
    name: str


@dataclass
class ScopeListResult:
    """Result of searching scopes."""

    items: list[ScopeData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass(frozen=True)
class SearchEntitiesParam:
    """Parameters for searching entities within a scope."""

    scope_type: ScopeType
    scope_id: str
    entity_type: EntityType
    querier: BatchQuerier
