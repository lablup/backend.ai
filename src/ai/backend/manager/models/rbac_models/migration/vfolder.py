import enum
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Self

from sqlalchemy.engine.row import Row

from ai.backend.manager.data.permission.association_scopes_entities import (
    AssociationScopesEntitiesCreateInput,
)
from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.data.permission.scope_permission import ScopePermissionCreateInput
from ai.backend.manager.models.vfolder import VFolderOwnershipType as OriginalVFolderOwnershipType
from ai.backend.manager.models.vfolder import VFolderPermission as OriginalVFolderPermission

from .enums import (
    OPERATIONS_FOR_CUSTOM_ROLE,
    OPERATIONS_FOR_SYSTEM_ROLE,
    EntityType,
    OperationType,
    RoleSource,
    ScopeType,
)
from .types import PermissionCreateInputGroup


class VFolderOwnershipType(enum.StrEnum):
    """
    Ownership type of virtual folder.
    """

    USER = "user"
    GROUP = "group"

    def to_original(self) -> OriginalVFolderOwnershipType:
        return OriginalVFolderOwnershipType(self.value)


class VFolderPermission(enum.StrEnum):
    """
    Mount permission for vfolder.
    Refer to `ai.backend.manager.models.vfolder.VFolderPermission`.
    """

    READ_ONLY = "ro"
    READ_WRITE = "rw"
    RW_DELETE = "wd"
    OWNER_PERM = "wd"  # resolved as RW_DELETE

    def to_original(self) -> OriginalVFolderPermission:
        return OriginalVFolderPermission(self.value)


@dataclass
class RoleData:
    id: uuid.UUID
    source: RoleSource

    @classmethod
    def from_row(cls, row: Row) -> Self:
        return cls(
            id=row.id,
            source=RoleSource(row.source),
        )


@dataclass
class ScopeData:
    type: ScopeType
    id: str

    @classmethod
    def from_row(cls, row: Row) -> Self:
        return cls(
            type=ScopeType(row.scope_type),
            id=row.scope_id,
        )

from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.data.permission.id import ObjectId, ScopeId

from .types import PermissionCreateInputGroup

ENTITY_TYPE = "vfolder"
ROLE_NAME_PREFIX = "vfolder_granted_"
OBJECT_PERMISSION_DEFAULT_OPERATION_VALUE = "read"


@dataclass
class VFolderData:
    id: uuid.UUID
    ownership_type: VFolderOwnershipType
    user_id: uuid.UUID | None
    group_id: uuid.UUID | None


@dataclass
class UserVFolderData:
    id: uuid.UUID
    user_id: uuid.UUID


@dataclass
class ProjectVFolderData:
    id: uuid.UUID
    project_id: uuid.UUID


@dataclass
class VFolderPermissionData:
    vfolder_id: uuid.UUID
    user_id: uuid.UUID
    mount_permission: VFolderPermission


vfolder_mount_permission_to_operation: Mapping[VFolderPermission, list[OperationType]] = {
    VFolderPermission.READ_ONLY: [OperationType.READ],
    VFolderPermission.READ_WRITE: [OperationType.READ, OperationType.UPDATE],
    VFolderPermission.RW_DELETE: [
        OperationType.READ,
        OperationType.UPDATE,
        OperationType.SOFT_DELETE,
        OperationType.HARD_DELETE,
    ],
    VFolderPermission.OWNER_PERM: [
        OperationType.READ,
        OperationType.UPDATE,
        OperationType.SOFT_DELETE,
        OperationType.HARD_DELETE,
    ],
}


def add_vfolder_scope_permissions_to_role(
    role: RoleData,
    scope: ScopeData,
) -> PermissionCreateInputGroup:
    """
    Add vfolder scope permissions to a role.
    This is used when a role is created or updated to include vfolder permissions.
    """
    match role.source:
        case RoleSource.SYSTEM:
            operations = OPERATIONS_FOR_SYSTEM_ROLE
        case RoleSource.CUSTOM:
            operations = OPERATIONS_FOR_CUSTOM_ROLE
    scope_permission_inputs = [
        ScopePermissionCreateInput(
            role_id=role.id,
            entity_type=EntityType.VFOLDER,
            operation=operation,
            scope_type=scope.type.to_original(),
            scope_id=scope.id,
        )
        for operation in operations
    ]
    return PermissionCreateInputGroup(
        scope_permissions=scope_permission_inputs,
    )


def map_vfolder_entity_to_scope(vfolder: VFolderData) -> PermissionCreateInputGroup:
    match vfolder.ownership_type:
        case VFolderOwnershipType.USER:
            scope_type = ScopeType.USER
            scope_id = str(vfolder.user_id)
        case VFolderOwnershipType.GROUP:
            scope_type = ScopeType.PROJECT
            scope_id = str(vfolder.group_id)
    association_input = AssociationScopesEntitiesCreateInput(
        scope_id=ScopeId(
            scope_type=scope_type.to_original(),
            scope_id=scope_id,
        ),
        object_id=ObjectId(
            entity_type=EntityType.VFOLDER.to_original(),
            entity_id=str(vfolder.id),
        ),
    )
    return PermissionCreateInputGroup(
        association_scopes_entities=[association_input],
    )


def map_vfolder_permission_data_to_scope(
    vfolder_permission: VFolderPermissionData,
) -> PermissionCreateInputGroup:
    association_input = AssociationScopesEntitiesCreateInput(
        scope_id=ScopeId(
            scope_type=ScopeType.USER.to_original(),
            scope_id=str(vfolder_permission.user_id),
        ),
        object_id=ObjectId(
            entity_type=EntityType.VFOLDER.to_original(),
            entity_id=str(vfolder_permission.vfolder_id),
        ),
    )
    return PermissionCreateInputGroup(
        association_scopes_entities=[association_input],
    )
