import enum
import uuid
from collections.abc import Mapping
from dataclasses import dataclass

from ai.backend.manager.data.permission.association_scopes_entities import (
    AssociationScopesEntitiesCreateInput,
)
from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.data.permission.object_permission import ObjectPermissionCreateInput
from ai.backend.manager.data.permission.scope_permission import ScopePermissionCreateInput
from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
    ScopeType,
)

from .types import PermissionCreateInputGroup


class VFolderPermission(enum.StrEnum):
    """
    Mount permission for vfolder.
    Refer to `ai.backend.manager.models.vfolder.VFolderPermission`.
    """

    READ_ONLY = "ro"
    READ_WRITE = "rw"
    RW_DELETE = "wd"
    OWNER_PERM = "wd"  # resolved as RW_DELETE


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


def map_user_vfolder_to_user_role(
    role_id: uuid.UUID,
    vfolder: UserVFolderData,
) -> PermissionCreateInputGroup:
    scope_permissions = [
        ScopePermissionCreateInput(
            role_id=role_id,
            scope_type=ScopeType.USER,
            scope_id=str(vfolder.user_id),
            entity_type=EntityType.VFOLDER,
            operation=str(operation),
        )
        for operation in OperationType
    ]
    association_scopes_entities = [
        AssociationScopesEntitiesCreateInput(
            scope_id=ScopeId(
                scope_type=ScopeType.USER,
                scope_id=str(vfolder.user_id),
            ),
            object_id=ObjectId(
                entity_type=EntityType.VFOLDER,
                entity_id=str(vfolder.id),
            ),
        )
    ]
    return PermissionCreateInputGroup(
        scope_permissions=scope_permissions,
        association_scopes_entities=association_scopes_entities,
    )


def map_project_vfolder_to_project_admin_role(
    role_id: uuid.UUID,
    vfolder: ProjectVFolderData,
) -> PermissionCreateInputGroup:
    scope_permissions = [
        ScopePermissionCreateInput(
            role_id=role_id,
            scope_type=ScopeType.PROJECT,
            scope_id=str(vfolder.project_id),
            entity_type=EntityType.VFOLDER,
            operation=str(operation),
        )
        for operation in OperationType
    ]
    association_scopes_entities = [
        AssociationScopesEntitiesCreateInput(
            scope_id=ScopeId(
                scope_type=ScopeType.PROJECT,
                scope_id=str(vfolder.project_id),
            ),
            object_id=ObjectId(
                entity_type=EntityType.VFOLDER,
                entity_id=str(vfolder.id),
            ),
        )
    ]
    return PermissionCreateInputGroup(
        scope_permissions=scope_permissions,
        association_scopes_entities=association_scopes_entities,
    )


def map_project_vfolder_to_project_user_role(
    role_id: uuid.UUID,
    vfolder: ProjectVFolderData,
) -> PermissionCreateInputGroup:
    scope_permissions = [
        ScopePermissionCreateInput(
            role_id=role_id,
            scope_type=ScopeType.PROJECT,
            scope_id=str(vfolder.project_id),
            entity_type=EntityType.VFOLDER,
            operation=OperationType.READ,
        )
    ]
    association_scopes_entities = [
        AssociationScopesEntitiesCreateInput(
            scope_id=ScopeId(
                scope_type=ScopeType.PROJECT,
                scope_id=str(vfolder.project_id),
            ),
            object_id=ObjectId(
                entity_type=EntityType.VFOLDER,
                entity_id=str(vfolder.id),
            ),
        )
    ]
    return PermissionCreateInputGroup(
        scope_permissions=scope_permissions,
        association_scopes_entities=association_scopes_entities,
    )


def map_vfolder_permission_data_to_user_role(
    role_id: uuid.UUID, vfolder_permission: VFolderPermissionData
) -> PermissionCreateInputGroup:
    object_permissions = [
        ObjectPermissionCreateInput(
            role_id=role_id,
            entity_type=EntityType.VFOLDER,
            entity_id=str(vfolder_permission.vfolder_id),
            operation=operation,
        )
        for operation in vfolder_mount_permission_to_operation[vfolder_permission.mount_permission]
    ]
    association_scopes_entities = [
        AssociationScopesEntitiesCreateInput(
            scope_id=ScopeId(
                scope_type=ScopeType.USER,
                scope_id=str(vfolder_permission.user_id),
            ),
            object_id=ObjectId(
                entity_type=EntityType.VFOLDER,
                entity_id=str(vfolder_permission.vfolder_id),
            ),
        )
    ]
    return PermissionCreateInputGroup(
        object_permissions=object_permissions,
        association_scopes_entities=association_scopes_entities,
    )
