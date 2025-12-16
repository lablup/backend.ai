from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .id import ObjectId, ScopeId
from .object_permission import (
    ObjectPermissionCreateInputBeforeRoleCreation,
    ObjectPermissionData,
)
from .permission_group import (
    PermissionGroupCreatorBeforeRoleCreation,
    PermissionGroupExtendedData,
)
from .status import RoleStatus
from .types import EntityType, OperationType, RoleSource


@dataclass(frozen=True)
class RoleCreateInput:
    name: str
    source: RoleSource = RoleSource.CUSTOM
    status: RoleStatus = RoleStatus.ACTIVE
    description: Optional[str] = None

    permission_groups: list[PermissionGroupCreatorBeforeRoleCreation] = field(default_factory=list)
    object_permissions: list[ObjectPermissionCreateInputBeforeRoleCreation] = field(
        default_factory=list
    )


@dataclass(frozen=True)
class RoleDeleteInput:
    id: uuid.UUID
    _status: RoleStatus = RoleStatus.DELETED


@dataclass(frozen=True)
class RoleData:
    id: uuid.UUID
    name: str
    source: RoleSource
    status: RoleStatus
    created_at: datetime
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]
    description: Optional[str] = None


@dataclass(frozen=True)
class RoleDataWithPermissions:
    id: uuid.UUID
    name: str
    source: RoleSource
    status: RoleStatus

    permission_groups: list[PermissionGroupExtendedData]
    object_permissions: list[ObjectPermissionData]

    created_at: datetime
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]
    description: Optional[str] = None


@dataclass(frozen=True)
class ScopePermissionCheckInput:
    user_id: uuid.UUID
    target_entity_type: EntityType
    target_scope_id: ScopeId
    operation: OperationType


@dataclass(frozen=True)
class SingleEntityPermissionCheckInput:
    user_id: uuid.UUID
    target_object_id: ObjectId
    operation: OperationType


@dataclass(frozen=True)
class BatchEntityPermissionCheckInput:
    user_id: uuid.UUID
    target_object_ids: list[ObjectId]
    operation: OperationType


@dataclass(frozen=True)
class UserRoleAssignmentInput:
    """
    Input to create a new user-role association.
    """

    user_id: uuid.UUID
    role_id: uuid.UUID
    granted_by: Optional[uuid.UUID] = None


@dataclass(frozen=True)
class UserRoleAssignmentData:
    user_id: uuid.UUID
    role_id: uuid.UUID
    granted_by: Optional[uuid.UUID] = None
