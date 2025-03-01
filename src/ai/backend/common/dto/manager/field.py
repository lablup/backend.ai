import enum
from typing import Optional

from pydantic import BaseModel

from ai.backend.common.types import VFolderUsageMode


class VFolderPermissionField(enum.StrEnum):
    READ_ONLY = "ro"
    READ_WRITE = "rw"
    RW_DELETE = "wd"
    OWNER_PERM = "wd"


class VFolderOperationStatusField(enum.StrEnum):
    READY = "ready"
    PERFORMING = "performing"
    CLONING = "cloning"
    MOUNTED = "mounted"
    ERROR = "error"

    DELETE_PENDING = "delete-pending"
    DELETE_ONGOING = "delete-ongoing"
    DELETE_COMPLETE = "delete-complete"
    DELETE_ERROR = "delete-error"


class VFolderOwnershipTypeField(enum.StrEnum):
    USER = "user"
    GROUP = "group"


class VFolderItemField(BaseModel):
    id: str
    name: str
    quota_scope_id: str
    host: str
    usage_mode: VFolderUsageMode
    created_at: str
    permission: VFolderPermissionField
    max_size: int
    creator: str
    ownership_type: VFolderOwnershipTypeField
    user: Optional[str]
    group: Optional[str]
    cloneable: bool
    status: VFolderOperationStatusField
    is_owner: bool
    user_email: str
    group_name: str
    type: str  # legacy
    max_files: int
    cur_size: int
