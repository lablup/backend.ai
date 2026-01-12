from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.data.permission.types import (
    GLOBAL_SCOPE_ID,
    EntityType,
    OperationType,
    RoleSource,
    ScopeType,
)

from .id import ScopeId

# Re-export types for easier access
__all__ = (
    "GLOBAL_SCOPE_ID",
    "EntityType",
    "OperationType",
    "RoleSource",
    "ScopeIDData",
    "ScopeIDListResult",
    "ScopeType",
)


@dataclass(frozen=True)
class ScopeIDData:
    """Data for a scope ID."""

    id: ScopeId
    name: str


@dataclass
class ScopeIDListResult:
    """Result of searching scope IDs."""

    items: list[ScopeIDData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
