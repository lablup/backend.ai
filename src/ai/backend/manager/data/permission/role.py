from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .id import ObjectId, ScopeId
from .object_permission import (
    ObjectPermissionCreateInput,
    ObjectPermissionData,
)
from .permission import ScopedPermissionCreateInput
from .permission_group import (
    PermissionGroupExtendedData,
)
from .status import RoleStatus
from .types import EntityType, OperationType, RoleSource


@dataclass(frozen=True)
class RoleData:
    """
    Information about a role.
    If detailed information is needed, use RoleDetailData.
    """

    id: uuid.UUID
    name: str
    source: RoleSource
    status: RoleStatus
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]
    description: Optional[str] = None


@dataclass(frozen=True)
class AssignedUserData:
    """Information about a user assigned to a role."""

    user_id: uuid.UUID
    granted_by: Optional[uuid.UUID]
    granted_at: datetime


@dataclass(frozen=True)
class RoleDetailData:
    """
    Detailed information about a role.
    It includes permission groups and object permissions.
    """

    id: uuid.UUID
    name: str
    source: RoleSource
    status: RoleStatus

    permission_groups: list[PermissionGroupExtendedData]
    object_permissions: list[ObjectPermissionData]

    created_at: datetime
    updated_at: datetime
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


@dataclass(frozen=True)
class RolePermissionsUpdateInput:
    """
    Input for batch updating role permissions.

    Uses scope-based permission management:
    - Scoped permissions are added using (scope_type, scope_id, entity_type, operation)
    - System automatically finds or creates permission groups by scope
    - All operations are performed in a single transaction

    Breaking Change from previous version:
    - Removed: add_permission_groups, remove_permission_group_ids, add_permissions, remove_permission_ids
    - Added: add_scoped_permissions, remove_scoped_permission_ids
    """

    role_id: uuid.UUID

    # Scoped permissions (automatic permission group management)
    add_scoped_permissions: list[ScopedPermissionCreateInput] = field(default_factory=list)
    remove_scoped_permission_ids: list[uuid.UUID] = field(default_factory=list)

    # Object permissions
    add_object_permissions: list[ObjectPermissionCreateInput] = field(default_factory=list)
    remove_object_permission_ids: list[uuid.UUID] = field(default_factory=list)


@dataclass(frozen=True)
class UserRoleRevocationInput:
    """
    Input to revoke a user-role association.
    """

    user_id: uuid.UUID
    role_id: uuid.UUID


@dataclass(frozen=True)
class UserRoleRevocationData:
    user_role_id: uuid.UUID
    user_id: uuid.UUID
    role_id: uuid.UUID


@dataclass(frozen=True)
class RoleListResult:
    """Result of role search with pagination info."""

    items: list[RoleData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass(frozen=True)
class AssignedUserListResult:
    """Result of assigned user search with pagination info."""

    items: list[AssignedUserData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
