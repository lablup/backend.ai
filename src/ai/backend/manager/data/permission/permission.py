from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from ai.backend.common.data.entity.types import EntityType, FieldData, ScopeType
from ai.backend.manager.data.common.types import SearchResult

from .types import OperationType, Permission


@dataclass
class PermissionCreator:
    role_id: uuid.UUID
    scope_type: ScopeType
    scope_id: str
    entity_type: EntityType
    operation: OperationType
    permission: Permission


@dataclass
class PermissionData(FieldData):
    id: uuid.UUID
    role_id: uuid.UUID
    scope_type: EntityType
    scope_id: str
    entity_type: EntityType
    operation: OperationType
    permission: Permission
    created_at: datetime


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


@dataclass(frozen=True)
class PermissionListResult(SearchResult[PermissionData]):
    """Result of scoped permission search with pagination info."""

    pass
