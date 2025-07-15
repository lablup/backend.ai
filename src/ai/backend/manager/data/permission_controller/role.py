import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from ai.backend.manager.types import OptionalState, TriState

from .object_permission import ObjectPermissionData
from .scope_permission import ScopePermissionData, ScopePermissionDataWithEntity
from .status import RoleStatus


@dataclass
class RoleCreateInput:
    name: str
    status: RoleStatus = RoleStatus.ACTIVE
    description: Optional[str] = None

    scope_permissions: list[ScopePermissionData] = field(default_factory=list)
    object_permissions: list[ObjectPermissionData] = field(default_factory=list)


@dataclass
class RoleUpdateInput:
    id: uuid.UUID
    name: OptionalState[str]
    status: OptionalState[RoleStatus]
    description: TriState[str]


@dataclass
class RoleDeleteInput:
    id: uuid.UUID
    _status: RoleStatus = RoleStatus.DELETED


@dataclass
class RoleData:
    id: uuid.UUID
    name: str
    status: RoleStatus
    created_at: datetime
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]
    description: Optional[str] = None


@dataclass
class RoleDataWithPermissions:
    id: uuid.UUID
    name: str
    status: RoleStatus

    scope_permissions: list[ScopePermissionDataWithEntity]
    object_permissions: list[ObjectPermissionData]

    created_at: datetime
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]
    description: Optional[str] = None


@dataclass
class PermissionCheckInput:
    user_id: uuid.UUID
    operation: str
    target_entity_type: str
    target_entity_id: str


@dataclass
class UserRoleAssignmentInput:
    user_id: uuid.UUID
    role_id: uuid.UUID
    granted_by: Optional[uuid.UUID] = None


@dataclass
class UserRoleAssignmentData:
    user_id: uuid.UUID
    role_id: uuid.UUID
    granted_by: Optional[uuid.UUID] = None
