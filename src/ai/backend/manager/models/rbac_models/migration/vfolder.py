import enum
import uuid
from collections.abc import Mapping
from typing import Optional

from ai.backend.manager.data.permission.types import EntityType
from ai.backend.manager.models.vfolder import VFolderOwnershipType as OriginalVFolderOwnershipType
from ai.backend.manager.models.vfolder import VFolderPermission as OriginalVFolderPermission

from .enums import (
    OperationType,
    RoleSource,
)
from .types import ScopeId, ScopeType

VFOLDER_ENTITY = EntityType.VFOLDER


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


vfolder_mount_permission_to_operation: Mapping[VFolderPermission, set[OperationType]] = {
    VFolderPermission.READ_ONLY: {OperationType.READ},
    VFolderPermission.READ_WRITE: {OperationType.READ, OperationType.UPDATE},
    VFolderPermission.RW_DELETE: {
        OperationType.READ,
        OperationType.UPDATE,
        OperationType.SOFT_DELETE,
        OperationType.HARD_DELETE,
    },
    VFolderPermission.OWNER_PERM: {
        OperationType.READ,
        OperationType.UPDATE,
        OperationType.SOFT_DELETE,
        OperationType.HARD_DELETE,
    },
}

role_source_to_operation: Mapping[RoleSource, set[OperationType]] = {
    RoleSource.SYSTEM: OperationType.owner_operations(),
    RoleSource.CUSTOM: OperationType.member_operations(),
}


def map_vfolder_entity_to_scope_id(
    ownership_type: VFolderOwnershipType,
    user_id: Optional[uuid.UUID],
    project_id: Optional[uuid.UUID],
) -> Optional[ScopeId]:
    """
    Map vfolder entity to ScopeId based on ownership type.
    """
    match ownership_type:
        case VFolderOwnershipType.USER:
            if user_id is None:
                return None
            return ScopeId(scope_type=ScopeType.USER.to_original(), scope_id=str(user_id))
        case VFolderOwnershipType.GROUP:
            if project_id is None:
                return None
            return ScopeId(scope_type=ScopeType.PROJECT.to_original(), scope_id=str(project_id))
