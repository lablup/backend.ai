import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import (
    Optional,
)

from ai.backend.manager.models.vfolder import QuotaScopeID, VFolderOperationStatus, VFolderUsageMode
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

    num_files: int
    used_bytes: int


@dataclass
class VFolderOwnershipInfo:
    creator_email: str


@dataclass
class VFolderUsageInfo:
    num_files: int
    used_bytes: int
