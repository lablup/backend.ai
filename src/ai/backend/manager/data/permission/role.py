import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, override

from ai.backend.manager.types import OptionalState, PartialModifier, TriState

from .id import ObjectId, ScopeId
from .object_permission import (
    ObjectPermissionCreateInputBeforeRoleCreation,
    ObjectPermissionData,
)
from .permission_group import PermissionGroupCreatorBeforeRoleCreation
from .status import RoleStatus
from .types import EntityType, OperationType, RoleSource


@dataclass
class RoleCreateInput:
    name: str
    source: RoleSource = RoleSource.CUSTOM
    status: RoleStatus = RoleStatus.ACTIVE
    description: Optional[str] = None

    permission_groups: list[PermissionGroupCreatorBeforeRoleCreation] = field(default_factory=list)
    object_permissions: list[ObjectPermissionCreateInputBeforeRoleCreation] = field(
        default_factory=list
    )


@dataclass
class RoleUpdateInput(PartialModifier):
    id: uuid.UUID
    name: OptionalState[str]
    source: OptionalState[RoleSource]
    status: OptionalState[RoleStatus]
    description: TriState[str]

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.source.update_dict(to_update, "source")
        self.status.update_dict(to_update, "status")
        self.description.update_dict(to_update, "description")
        return to_update


@dataclass
class RoleDeleteInput:
    id: uuid.UUID
    _status: RoleStatus = RoleStatus.DELETED


@dataclass
class RoleData:
    id: uuid.UUID
    name: str
    source: RoleSource
    status: RoleStatus
    created_at: datetime
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]
    description: Optional[str] = None


@dataclass
class RoleDataWithPermissions:
    id: uuid.UUID
    name: str
    source: RoleSource
    status: RoleStatus

    object_permissions: list[ObjectPermissionData]

    created_at: datetime
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]
    description: Optional[str] = None


@dataclass
class ScopePermissionCheckInput:
    user_id: uuid.UUID
    target_entity_type: EntityType
    target_scope_id: ScopeId
    operation: OperationType


@dataclass
class SingleEntityPermissionCheckInput:
    user_id: uuid.UUID
    target_object_id: ObjectId
    operation: OperationType


@dataclass
class UserRoleAssignmentInput:
    """
    Input to create a new user-role association.
    """

    user_id: uuid.UUID
    role_id: uuid.UUID
    granted_by: Optional[uuid.UUID] = None


@dataclass
class UserRoleAssignmentData:
    user_id: uuid.UUID
    role_id: uuid.UUID
    granted_by: Optional[uuid.UUID] = None
