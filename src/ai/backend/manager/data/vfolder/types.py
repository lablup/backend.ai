import enum
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ai.backend.common.types import QuotaScopeID, VFolderID, VFolderUsageMode
from ai.backend.manager.models.vfolder import (
    VFolderOperationStatus,
    VFolderOwnershipType,
    VFolderPermission,
)


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
    permission: Optional[VFolderPermission]
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
    permission: VFolderPermission


@dataclass
class VFolderInvitationData:
    """
    VFolder invitation data representing invitations to share VFolders.
    """

    id: uuid.UUID
    vfolder: uuid.UUID
    inviter: str  # email
    invitee: str  # email
    permission: VFolderPermission
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
    permission: VFolderPermission
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
    effective_permission: VFolderPermission


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
