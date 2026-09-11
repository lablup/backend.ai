from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.permission.types import (
    GLOBAL_SCOPE_ID,
    Permission,
    RoleSource,
    role_scope_types,
)
from ai.backend.manager.data.common.types import SearchResult

from .id import ScopeId

# Re-export types for easier access
__all__ = (
    "GLOBAL_SCOPE_ID",
    "EntityType",
    "GrantableOperation",
    "Permission",
    "RBACElementRef",
    "RoleSource",
    "ScopeData",
    "ScopeListResult",
    "role_scope_types",
)


@dataclass(frozen=True)
class GrantableOperation:
    """One operation a role may permit, as the ops wiring declares it."""

    name: str
    description: str
    permission: Permission


@dataclass(frozen=True)
class RBACElementRef:
    """Reference to an element in the RBAC scope-entity relationship model."""

    element_type: EntityType
    element_id: str

    @classmethod
    def from_str(cls, val: str) -> Self:
        element_type, _, element_id = val.partition(":")
        return cls(element_type=EntityType.from_name(element_type), element_id=element_id)

    def to_str(self) -> str:
        return f"{self.element_type}:{self.element_id}"

    def to_scope_id(self) -> ScopeId:
        return ScopeId(scope_type=self.element_type, scope_id=self.element_id)


@dataclass(frozen=True)
class ScopeData:
    """Data for a scope."""

    id: ScopeId
    name: str


@dataclass(frozen=True)
class ScopeListResult(SearchResult[ScopeData]):
    """Result of searching scopes."""

    pass
