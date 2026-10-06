from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Final, override

from ai.backend.common.data.entity.types import EntityData, EntityIdentifier, FieldData
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.data.entity.vfolder_mount_policy import VFolderMountPolicyID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.defs import RESERVED_VFOLDER_PATTERNS, RESERVED_VFOLDERS
from ai.backend.common.dto.manager.field import (
    VFolderOperationStatusField,
    VFolderOwnershipTypeField,
    VFolderPermissionField,
)
from ai.backend.common.types import (
    CIStrEnum,
    QuotaScopeID,
    VFolderHostPermissionMap,
    VFolderID,
    VFolderMountPolicy,
    VFolderUsageMode,
)
from ai.backend.manager.errors.resource import DataTransformationFailed


def verify_vfolder_name(folder: str) -> bool:
    if folder in RESERVED_VFOLDERS:
        return False
    for pattern in RESERVED_VFOLDER_PATTERNS:
        if pattern.match(folder):
            return False
    return True


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
    def _missing_(cls, value: Any) -> VFolderMountPermission | None:
        if not isinstance(value, str):
            raise DataTransformationFailed(
                f"VFolderMountPermission value must be a string, got {type(value).__name__}"
            )
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
    CREATING = "creating"
    PERFORMING = "performing"
    CLONING = "cloning"
    MOUNTED = "mounted"
    ERROR = "error"

    DELETE_PENDING = "delete-pending"  # vfolder is in trash bin
    DELETE_ONGOING = "delete-ongoing"  # vfolder is being deleted in storage
    DELETE_COMPLETE = "delete-complete"  # vfolder is deleted permanently, only DB row remains
    DELETE_ERROR = "delete-error"

    @classmethod
    def purge_in_progress(cls) -> frozenset[VFolderOperationStatus]:
        """Statuses a purge is working through. Writes are refused while in one.

        ``DELETE_ONGOING`` and ``DELETE_ERROR`` name the two points the other entities
        call ``purging`` and ``purge-error``.
        """
        return frozenset({cls.DELETE_ONGOING, cls.DELETE_ERROR})

    @classmethod
    def hard_deleted(cls) -> frozenset[VFolderOperationStatus]:
        """Statuses of a folder whose storage is gone or failed to go; only its row remains."""
        return frozenset({cls.DELETE_COMPLETE, cls.DELETE_ERROR})

    @classmethod
    def dead(cls) -> frozenset[VFolderOperationStatus]:
        """Statuses of a folder in the trash or past it, which no session may mount."""
        return frozenset({
            cls.DELETE_PENDING,
            cls.DELETE_ONGOING,
            cls.DELETE_COMPLETE,
            cls.DELETE_ERROR,
        })

    @override
    @classmethod
    def _missing_(cls, value: Any) -> VFolderOperationStatus | None:
        if not isinstance(value, str):
            raise DataTransformationFailed(
                f"VFolderOperationStatus value must be a string, got {type(value).__name__}"
            )
        match value.upper():
            case "READY":
                return cls.READY
            case "CREATING":
                return cls.CREATING
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
        return self == VFolderOperationStatus.DELETE_PENDING

    def to_field(self) -> VFolderOperationStatusField:
        return VFolderOperationStatusField(self)


class VFolderStatusSet(enum.StrEnum):
    """
    Acts as an alias to represent set of VFolder statuses. Use this value as a key of
    `vfolder_status_map` dictionary to retrieve actual `VFolderOperationStatus` values.
    """

    ALL = "all"
    """Represents VFolder in all state"""

    READABLE = "readable"
    """Represents VFolder in a normal (readable, mountable and clonable) state"""

    MOUNTABLE = "mountable"
    """Represents VFolder in a mountable state"""

    UPDATABLE = "updatable"
    """Represents VFolder in idle (not performing active clone or removal) state"""

    DELETABLE = "deletable"
    """Simillar with UPDATABLE but does not allow VFolder in MOUNTED state"""

    PURGABLE = "purgable"
    """Represents VFolder located in trash bin. The meaning of `purge` here is
    completely different between our VFolder `/purge` API so be sure not to confuse.
    That API will be renamed any soon in a more self-representitive way."""

    RECOVERABLE = "recoverable"
    """alias of VFolderStatusSet.PURGABLE"""

    INACCESSIBLE = "inaccessible"
    """Represents VFolder which is now completely removed from storage and only its record is being kept"""

    OWNER_PURGABLE = "owner-purgable"
    """Represents VFolder whose storage payload must be reclaimed when its owning
    user or group is purged. Unlike DELETABLE, this includes folders in the trash
    bin and folders whose previous deletion stalled or failed, since the owner row
    is removed right after and any skipped folder becomes a permanent orphan."""


vfolder_status_map: Final[dict[VFolderStatusSet, set[VFolderOperationStatus]]] = {
    VFolderStatusSet.ALL: {
        VFolderOperationStatus.READY,
        VFolderOperationStatus.CREATING,
        VFolderOperationStatus.PERFORMING,
        VFolderOperationStatus.CLONING,
        VFolderOperationStatus.MOUNTED,
        VFolderOperationStatus.ERROR,
        VFolderOperationStatus.DELETE_PENDING,
        VFolderOperationStatus.DELETE_ONGOING,
        VFolderOperationStatus.DELETE_COMPLETE,
        VFolderOperationStatus.DELETE_ERROR,
    },
    VFolderStatusSet.READABLE: {
        VFolderOperationStatus.READY,
        VFolderOperationStatus.PERFORMING,
        VFolderOperationStatus.CLONING,
        VFolderOperationStatus.MOUNTED,
        VFolderOperationStatus.ERROR,
        VFolderOperationStatus.DELETE_PENDING,
    },
    VFolderStatusSet.MOUNTABLE: {
        VFolderOperationStatus.READY,
        VFolderOperationStatus.PERFORMING,
        VFolderOperationStatus.CLONING,
        VFolderOperationStatus.MOUNTED,
    },
    # if UPDATABLE access status is requested, READY and MOUNTED operation statuses are accepted.
    VFolderStatusSet.UPDATABLE: {
        VFolderOperationStatus.READY,
        VFolderOperationStatus.MOUNTED,
    },
    # if DELETABLE access status is requested, only READY operation status is accepted.
    VFolderStatusSet.DELETABLE: {
        VFolderOperationStatus.READY,
    },
    # if DELETABLE access status is requested, DELETE_PENDING, DELETE_COMPLETE operation status is accepted.
    # CREATING is purgable: the row is there but its storage folder may not be, and
    # nobody can have used it — a readable or mountable state it never was.
    VFolderStatusSet.PURGABLE: {
        VFolderOperationStatus.CREATING,
        VFolderOperationStatus.DELETE_PENDING,
        VFolderOperationStatus.DELETE_COMPLETE,
    },
    VFolderStatusSet.RECOVERABLE: {
        VFolderOperationStatus.DELETE_PENDING,
    },
    VFolderStatusSet.INACCESSIBLE: {
        VFolderOperationStatus.DELETE_COMPLETE,
    },
    # DELETE_COMPLETE is excluded: its storage payload is already gone, so there
    # is nothing left to reclaim on owner purge.
    VFolderStatusSet.OWNER_PURGABLE: {
        VFolderOperationStatus.READY,
        VFolderOperationStatus.CREATING,
        VFolderOperationStatus.DELETE_PENDING,
        VFolderOperationStatus.DELETE_ONGOING,
        VFolderOperationStatus.DELETE_ERROR,
    },
}


@dataclass(frozen=True)
class UserWithVFolderHostPermissions:
    """
    Minimal user fields paired with the union of ``allowed_vfolder_hosts``
    across the user's active keypair resource policies. The host permission
    map is the merged set used for vfolder host-permission validation.
    """

    email: str
    role: UserRole
    allowed_vfolder_hosts: VFolderHostPermissionMap


@dataclass
class VFolderData(EntityData):
    """
    Complete VFolder data representing all VFolder properties.
    Used by repository layer for returning full VFolder information.
    """

    id: VFolderUUID
    name: str
    host: str
    domain_name: str
    quota_scope_id: QuotaScopeID | None
    usage_mode: VFolderUsageMode
    default_mount_permission: VFolderMountPolicy
    created_at: datetime
    last_used: datetime | None
    updated_at: datetime
    creator: str | None
    creator_id: uuid.UUID | None
    unmanaged_path: str | None
    ownership_type: VFolderOwnershipType
    user: uuid.UUID | None
    group: uuid.UUID | None
    cloneable: bool
    status: VFolderOperationStatus

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.id


@dataclass
class VFolderUsageData:
    """
    Usage measurements fetched live from the storage proxy.
    """

    num_files: int
    used_bytes: int


@dataclass
class VFolderMountPolicyData(FieldData):
    """The mount level one user gets on a vfolder."""

    id: VFolderMountPolicyID
    vfolder_id: VFolderUUID
    user_id: uuid.UUID
    permission: VFolderMountPolicy
    created_at: datetime
    updated_at: datetime


@dataclass
class VFolderInvitationData:
    """
    VFolder invitation data representing invitations to share VFolders.
    """

    id: uuid.UUID
    vfolder: uuid.UUID
    inviter: str  # email
    inviter_username: str | None
    invitee: str  # email
    permission: VFolderMountPolicy
    created_at: datetime
    modified_at: datetime | None


@dataclass
class VFolderCreation:
    """A vfolder row that landed, and what making its storage folder needs.

    The quota the folder is made with and the uid its files take belong to the owner's
    resource policy, which the row does not carry; they are read where the row is
    written so the storage step needs nothing more.
    """

    vfolder: VFolderData
    max_quota_scope_size: int
    container_uid: int | None


@dataclass
class VFolderLocation:
    """
    Minimal VFolder location information for storage access.
    Contains only the essential fields needed to locate and access a vfolder in storage.
    """

    id: uuid.UUID
    quota_scope_id: QuotaScopeID | None
    host: str
    ownership_type: VFolderOwnershipType
    usage_mode: VFolderUsageMode = VFolderUsageMode.GENERAL


@dataclass
class VFolderStorageTarget:
    """Where a vfolder lives in storage: its id, its host and an unmanaged path if it has one."""

    vfolder_id: VFolderID
    host: str
    unmanaged_path: str | None


@dataclass
class VFolderCloneInfo:
    source_vfolder_id: VFolderID
    source_host: str
    unmanaged_path: str | None
    domain_name: str

    # Target Vfolder infos
    target_quota_scope_id: QuotaScopeID
    target_vfolder_name: str
    target_host: str
    usage_mode: VFolderUsageMode
    permission: VFolderMountPolicy
    email: str
    user_id: uuid.UUID
    cloneable: bool
