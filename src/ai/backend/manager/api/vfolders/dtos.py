import uuid
from dataclasses import dataclass
from typing import Any, Mapping, Optional

from ai.backend.common.types import QuotaScopeID, VFolderUsageMode
from ai.backend.manager.models import (
    ProjectType,
    VFolderOperationStatus,
    VFolderOwnershipType,
    VFolderPermission,
)


@dataclass
class UserIdentity:
    user_uuid: uuid.UUID
    user_role: str
    user_email: str
    domain_name: str


@dataclass
class Keypair:
    access_key: str
    resource_policy: Mapping[str, Any]


@dataclass
class UserScopeInput:
    requester_id: uuid.UUID
    is_authorized: bool
    is_superadmin: bool
    delegate_email: Optional[str] = None


@dataclass
class VFolderCreateRequirements:
    name: str
    folder_host: Optional[str]
    usage_mode: VFolderUsageMode
    permission: VFolderPermission
    group_id: Optional[uuid.UUID]
    cloneable: bool
    unmanaged_path: Optional[str]


@dataclass
class VFolderMetadata:
    id: str
    name: str
    quota_scope_id: QuotaScopeID
    host: str
    usage_mode: VFolderUsageMode
    created_at: str
    permission: VFolderPermission
    max_size: int  # migrated to quota scopes, no longer valid
    creator: str
    ownership_type: VFolderOwnershipType
    user: Optional[str]
    group: Optional[str]
    cloneable: bool
    status: VFolderOperationStatus


@dataclass
class VFolderListItem:
    id: str
    name: str
    quota_scope_id: str
    host: str
    usage_mode: VFolderUsageMode
    created_at: str
    permission: VFolderPermission
    max_size: int
    creator: str
    ownership_type: VFolderOwnershipType
    user: Optional[str]
    group: Optional[str]
    cloneable: bool
    status: VFolderOperationStatus
    is_owner: bool
    user_email: str
    group_name: str
    type: str  # legacy
    max_files: int
    cur_size: int


@dataclass
class VFolderList:
    entries: list[VFolderListItem]


@dataclass
class VFolderCapabilityInfo:
    max_vfolder_count: int
    max_quota_scope_size: int
    ownership_type: str
    quota_scope_id: QuotaScopeID
    group_uuid: Optional[uuid.UUID] = None
    group_type: Optional[ProjectType] = None
