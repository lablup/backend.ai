from __future__ import annotations

import uuid
from dataclasses import dataclass

from .id import ScopeId
from .types import EntityType, OperationType, ScopeType


@dataclass
class PermissionCreator:
    role_id: uuid.UUID
    scope_type: ScopeType
    scope_id: str
    entity_type: EntityType
    operation: OperationType


@dataclass
class PermissionData:
    id: uuid.UUID
    role_id: uuid.UUID
    scope_type: ScopeType
    scope_id: str
    entity_type: EntityType
    operation: OperationType


@dataclass
class ScopedPermissionCreateInput:
    """
    Input for creating a scoped permission using scope information.
    Used in update_role_permissions API to add permissions by scope.
    """

    scope_type: ScopeType
    scope_id: str
    entity_type: EntityType
    operation: OperationType

    def to_scope_id(self) -> ScopeId:
        """Convert to ScopeId."""
        return ScopeId(scope_type=self.scope_type, scope_id=self.scope_id)


@dataclass(frozen=True)
class PermissionListResult:
    """Result of scoped permission search with pagination info."""

    items: list[PermissionData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
