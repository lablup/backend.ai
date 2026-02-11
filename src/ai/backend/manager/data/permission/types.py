from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.data.permission.types import (
    GLOBAL_SCOPE_ID,
    EntityType,
    FieldType,
    OperationType,
    RelationType,
    RoleSource,
    ScopeType,
)
from ai.backend.manager.data.common.types import SearchResult

from .id import ScopeId

# Re-export types for easier access
__all__ = (
    "GLOBAL_SCOPE_ID",
    "EntityType",
    "FieldType",
    "OperationType",
    "RelationType",
    "RoleSource",
    "ScopeData",
    "ScopeListResult",
    "ScopeType",
)


@dataclass(frozen=True)
class ScopeData:
    """Data for a scope."""

    id: ScopeId
    name: str


@dataclass(frozen=True)
class ScopeListResult(SearchResult[ScopeData]):
    """Result of searching scopes."""

    pass
