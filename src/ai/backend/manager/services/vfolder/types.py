import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import (
    Optional,
)

from ai.backend.manager.models.vfolder import (
    QuotaScopeID,
    VFolderOperationStatus,
    VFolderOwnershipType,
    VFolderUsageMode,
)
from ai.backend.manager.models.vfolder import VFolderPermission as VFolderMountPermission


@dataclass
class VFolderBaseInfo:
    id: uuid.UUID
    quota_scope_id: Optional[QuotaScopeID]
    name: str
    host: str
    status: VFolderOperationStatus
    unmanaged_path: Optional[str]
    mount_permission: VFolderMountPermission
    usage_mode: VFolderUsageMode
    created_at: datetime
    cloneable: bool


@dataclass
class VFolderOwnershipInfo:
    creator_email: str
    is_owner: bool
    ownership_type: VFolderOwnershipType
    user_uuid: Optional[uuid.UUID]
    group_uuid: Optional[uuid.UUID]


@dataclass
class VFolderUsageInfo:
    num_files: int
    used_bytes: int


@dataclass
class VFolderInvitationInfo:
    id: uuid.UUID
    vfolder_id: uuid.UUID
    vfolder_name: str
    invitee_user_email: str
    inviter_user_email: str
    mount_permission: VFolderMountPermission
    created_at: datetime
    modified_at: datetime
    status: VFolderOperationStatus


@dataclass
class FileInfo:
    name: str
    type: str
    size: int
    mode: str
    created: str
    modified: str
