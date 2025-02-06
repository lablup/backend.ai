import enum
from typing import Optional

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.dto import VFolderPermissionDTO
from ai.backend.common.types import VFolderUsageMode


class VFolderOperationStatusRes(enum.StrEnum):
    READY = "ready"
    PERFORMING = "performing"
    CLONING = "cloning"
    MOUNTED = "mounted"
    ERROR = "error"

    DELETE_PENDING = "delete-pending"
    DELETE_ONGOING = "delete-ongoing"
    DELETE_COMPLETE = "delete-complete"
    DELETE_ERROR = "delete-error"


class VFolderCreateResponse(BaseResponseModel):
    id: str
    name: str
    quota_scope_id: str
    host: str
    usage_mode: VFolderUsageMode
    permission: VFolderPermissionDTO
    max_size: int = 0  # migrated to quota scopes, no longer valid
    creator: str
    ownership_type: str
    user: Optional[str]
    group: Optional[str]
    cloneable: bool
    status: VFolderOperationStatusRes = Field(default=VFolderOperationStatusRes.READY)


class VFolderOwnershipTypeRes(enum.StrEnum):
    USER = "user"
    GROUP = "group"


class VFolderListItemRes(BaseResponseModel):  # TODO: Why VFolderListItem is needed?
    id: str
    name: str
    quota_scope_id: str
    host: str
    usage_mode: VFolderUsageMode
    created_at: str
    permission: VFolderPermissionDTO
    max_size: int
    creator: str
    ownership_type: VFolderOwnershipTypeRes
    user: Optional[str]
    group: Optional[str]
    cloneable: bool
    status: VFolderOperationStatusRes
    is_owner: bool
    user_email: str
    group_name: str
    type: str  # legacy
    max_files: int
    cur_size: int


class VFolderListResponse(BaseResponseModel):
    items: list[VFolderListItemRes] = Field(default_factory=list)
