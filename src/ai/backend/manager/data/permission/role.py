import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, override

from ai.backend.manager.types import OptionalState, PartialModifier, TriState

from .object_permission import ObjectPermissionData
from .scope_permission import ScopePermissionData
from .status import RoleStatus
from .types import EntityType, RoleSource


@dataclass
class RoleCreateInput:
    name: str
    source: RoleSource = RoleSource.CUSTOM
    status: RoleStatus = RoleStatus.ACTIVE
    description: Optional[str] = None

    scope_permissions: list[ScopePermissionData] = field(default_factory=list)
    object_permissions: list[ObjectPermissionData] = field(default_factory=list)


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
class PermissionCheckInput:
    user_id: uuid.UUID
    operation: str
    target_entity_type: EntityType
    target_entity_id: str


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
