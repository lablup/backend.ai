from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from ai.backend.common.data.entity.types import EntityType, ScopeType
from ai.backend.manager.data.common.types import SearchResult

from .types import Permission


@dataclass
class PermissionCreator:
    role_id: uuid.UUID
    scope_type: ScopeType
    scope_id: str
    entity_type: EntityType
    permission: Permission


@dataclass
class PermissionData:
    id: uuid.UUID
    role_id: uuid.UUID
    scope_type: EntityType
    scope_id: str
    entity_type: EntityType
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
    permission: Permission


@dataclass(frozen=True)
class PermissionListResult(SearchResult[PermissionData]):
    """Result of scoped permission search with pagination info."""

    pass
