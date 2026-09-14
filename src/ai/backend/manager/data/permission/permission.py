from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from ai.backend.common.data.entity.permission import PermissionID
from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import EntityType, FieldData
from ai.backend.manager.data.common.types import SearchResult

from .types import Permission


@dataclass
class PermissionCreator:
    role_id: uuid.UUID
    entity_type: EntityType
    permission: Permission


@dataclass
class PermissionData(FieldData):
    id: PermissionID
    role_id: RoleID
    entity_type: EntityType
    permission: Permission
    created_at: datetime


@dataclass(frozen=True)
class PermissionListResult(SearchResult[PermissionData]):
    """Result of scoped permission search with pagination info."""

    pass
