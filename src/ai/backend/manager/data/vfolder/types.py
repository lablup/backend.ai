from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, override

from ai.backend.common.dto.manager.field import (
    VFolderOperationStatusField,
    VFolderOwnershipTypeField,
    VFolderPermissionField,
)
from ai.backend.common.types import CIStrEnum, QuotaScopeID, VFolderID, VFolderUsageMode

from ..permission.types import OperationType


class VFolderOwnershipType(CIStrEnum):
    """
    Ownership type of virtual folder.
    """

    USER = "user"
    GROUP = "group"

    def to_field(self) -> VFolderOwnershipTypeField:
        return VFolderOwnershipTypeField(self)


class VFolderMountPermission(enum.StrEnum):
    # TODO: Replace this class with VFolderRBACPermission
    # Or rename this class to VFolderMountPermission
    """
    Permissions for a virtual folder given to a specific access key.
    RW_DELETE includes READ_WRITE and READ_WRITE includes READ_ONLY.
    """

    READ_ONLY = "ro"
    READ_WRITE = "rw"
    RW_DELETE = "wd"
    OWNER_PERM = "wd"  # resolved as RW_DELETE

    def to_field(self) -> VFolderPermissionField:
        return VFolderPermissionField(self)

    @override
    @classmethod
    def _missing_(cls, value: Any) -> Optional[VFolderMountPermission]:
        assert isinstance(value, str)
        match value.upper():
            case "RO" | "READ_ONLY":
                return cls.READ_ONLY
            case "RW" | "READ_WRITE":
                return cls.READ_WRITE
            case "RW_DELETE":
                return cls.RW_DELETE
            case "WD" | "OWNER_PERM":
                return cls.OWNER_PERM
        return None

    def to_rbac_operation(self) -> set[OperationType]:
        match self:
            case VFolderMountPermission.READ_ONLY:
                return {OperationType.READ}
            case VFolderMountPermission.READ_WRITE:
                return {OperationType.READ, OperationType.UPDATE, OperationType.SOFT_DELETE}
            case VFolderMountPermission.RW_DELETE | VFolderMountPermission.OWNER_PERM:
                return {OperationType.READ, OperationType.UPDATE, OperationType.SOFT_DELETE}
        return set()


class VFolderInvitationState(enum.StrEnum):
    """
    Virtual Folder invitation state.
    """

    PENDING = "pending"
    CANCELED = "canceled"  # canceled by inviter
    ACCEPTED = "accepted"
    REJECTED = "rejected"  # rejected by invitee


class VFolderOperationStatus(enum.StrEnum):
    """
    Introduce virtual folder current status for storage-proxy operations.
    """

    READY = "ready"
    PERFORMING = "performing"
    CLONING = "cloning"
    MOUNTED = "mounted"
    ERROR = "error"

    DELETE_PENDING = "delete-pending"  # vfolder is in trash bin
    DELETE_ONGOING = "delete-ongoing"  # vfolder is being deleted in storage
    DELETE_COMPLETE = "delete-complete"  # vfolder is deleted permanently, only DB row remains
    DELETE_ERROR = "delete-error"

    @override
    @classmethod
    def _missing_(cls, value: Any) -> Optional[VFolderOperationStatus]:
        assert isinstance(value, str)
        match value.upper():
            case "READY":
                return cls.READY
            case "PERFORMING":
                return cls.PERFORMING
            case "CLONING":
                return cls.CLONING
            case "MOUNTED":
                return cls.MOUNTED
            case "ERROR":
                return cls.ERROR
            case "DELETE_PENDING" | "DELETE-PENDING":
                return cls.DELETE_PENDING
            case "DELETE_ONGOING" | "DELETE-ONGOING":
                return cls.DELETE_ONGOING
            case "DELETE_COMPLETE" | "DELETE-COMPLETE":
                return cls.DELETE_COMPLETE
            case "DELETE_ERROR" | "DELETE-ERROR":
                return cls.DELETE_ERROR
        return None

    def is_deletable(self, force: bool = False) -> bool:
        if force:
            return self in {
                VFolderOperationStatus.READY,
                VFolderOperationStatus.DELETE_PENDING,
                VFolderOperationStatus.DELETE_ONGOING,
                VFolderOperationStatus.DELETE_ERROR,
            }
        else:
            return self == VFolderOperationStatus.DELETE_PENDING

    def to_field(self) -> VFolderOperationStatusField:
        return VFolderOperationStatusField(self)


@dataclass
class VFolderData:
    """
    Complete VFolder data representing all VFolder properties.
    Used by repository layer for returning full VFolder information.
    """

    id: uuid.UUID
    name: str
    host: str
    domain_name: str
    quota_scope_id: Optional[QuotaScopeID]
    usage_mode: VFolderUsageMode
    permission: Optional[VFolderMountPermission]
    max_files: int
    max_size: Optional[int]
    num_files: int
    cur_size: int
    created_at: datetime
    last_used: Optional[datetime]
    creator: Optional[str]
    unmanaged_path: Optional[str]
    ownership_type: VFolderOwnershipType
    user: Optional[uuid.UUID]
    group: Optional[uuid.UUID]
    cloneable: bool
    status: VFolderOperationStatus


@dataclass
class VFolderPermissionData:
    """
    VFolder permission data representing user-specific permissions on a VFolder.
    """

    id: uuid.UUID
    vfolder: uuid.UUID
    user: uuid.UUID
    permission: VFolderMountPermission


@dataclass
class VFolderInvitationData:
    """
    VFolder invitation data representing invitations to share VFolders.
    """

    id: uuid.UUID
    vfolder: uuid.UUID
    inviter: str  # email
    invitee: str  # email
    permission: VFolderMountPermission
    created_at: datetime
    modified_at: Optional[datetime]


@dataclass
class VFolderCreateParams:
    """
    Parameters needed to create a new VFolder.
    """

    id: uuid.UUID
    name: str
    domain_name: str
    quota_scope_id: str
    usage_mode: VFolderUsageMode
    permission: VFolderMountPermission
    host: str
    creator: str
    ownership_type: VFolderOwnershipType
    user: Optional[uuid.UUID]
    group: Optional[uuid.UUID]
    unmanaged_path: Optional[str]
    cloneable: bool
    status: VFolderOperationStatus


@dataclass
class VFolderAccessInfo:
    """
    Information about VFolder access for query results.
    """

    vfolder_data: VFolderData
    is_owner: bool
    effective_permission: VFolderMountPermission


@dataclass
class VFolderListResult:
    """
    Result of VFolder list operations with pagination support.
    """

    vfolders: list[VFolderAccessInfo]
    total_count: Optional[int] = None


@dataclass
class VFolderDeleteParams:
    vfolder_id: VFolderID
    host: str
    unmanaged_path: Optional[str] = None


class DeleteStatus(enum.StrEnum):
    DELETE_ONGOING = "delete_ongoing"
    ALREADY_DELETED = "already_deleted"
    ERROR = "error"


@dataclass
class VFolderDeleteResult:
    """
    Result of a VFolder delete operation.
    """

    vfolder_id: VFolderID
    status: DeleteStatus


@dataclass
class VFolderLocation:
    """
    Minimal VFolder location information for storage access.
    Contains only the essential fields needed to locate and access a vfolder in storage.
    """

    id: uuid.UUID
    quota_scope_id: Optional[QuotaScopeID]
    host: str
    ownership_type: VFolderOwnershipType
