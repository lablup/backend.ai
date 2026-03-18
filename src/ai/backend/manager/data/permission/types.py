from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from ai.backend.common.data.permission.types import (
    GLOBAL_SCOPE_ID,
    EntityType,
    FieldType,
    OperationType,
    RBACElementType,
    RelationType,
    RoleSource,
    ScopeType,
)
from ai.backend.manager.data.common.types import SearchResult

from .id import ObjectId, ScopeId

# Re-export types for easier access
__all__ = (
    "GLOBAL_SCOPE_ID",
    "EntityType",
    "FieldType",
    "OperationType",
    "RBACElementType",
    "RBACElementRef",
    "RelationType",
    "RoleSource",
    "ScopeData",
    "ScopeListResult",
    "ScopeType",
)


@dataclass(frozen=True)
class RBACElementRef:
    """Reference to an element in the RBAC scope-entity relationship model."""

    element_type: RBACElementType
    element_id: str

    @classmethod
    def from_str(cls, val: str) -> Self:
        element_type, _, element_id = val.partition(":")
        return cls(element_type=RBACElementType(element_type), element_id=element_id)

    def to_str(self) -> str:
        return f"{self.element_type}:{self.element_id}"

    def to_scope_id(self) -> ScopeId:
        """Bridge to ScopeId for layers that still use ScopeType."""
        return ScopeId(scope_type=self.element_type.to_scope_type(), scope_id=self.element_id)

    def to_object_id(self) -> ObjectId:
        """Bridge to ObjectId for layers that still use EntityType."""
        return ObjectId(entity_type=self.element_type.to_entity_type(), entity_id=self.element_id)


@dataclass(frozen=True)
class ScopeData:
    """Data for a scope."""

    id: ScopeId
    name: str


@dataclass(frozen=True)
class ScopeListResult(SearchResult[ScopeData]):
    """Result of searching scopes."""

    pass
