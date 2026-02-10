from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.data.permission.exceptions import InvalidTypeConversionError
from ai.backend.common.data.permission.types import (
    ENTITY_GRAPH,
    ENTITY_TO_SCOPE_MAP,
    GLOBAL_SCOPE_ID,
    SCOPE_TO_ENTITY_MAP,
    EntityType,
    FieldType,
    OperationType,
    RelationType,
    RoleSource,
    ScopeType,
    entity_type_to_scope_type,
    get_relation_type,
    scope_type_to_entity_type,
)

from .id import ScopeId

# Re-export types for easier access
__all__ = (
    "ENTITY_GRAPH",
    "ENTITY_TO_SCOPE_MAP",
    "GLOBAL_SCOPE_ID",
    "InvalidTypeConversionError",
    "SCOPE_TO_ENTITY_MAP",
    "EntityType",
    "FieldType",
    "OperationType",
    "RelationType",
    "RoleSource",
    "ScopeData",
    "ScopeListResult",
    "ScopeType",
    "entity_type_to_scope_type",
    "get_relation_type",
    "scope_type_to_entity_type",
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
