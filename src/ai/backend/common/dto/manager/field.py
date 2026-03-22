import enum

from ai.backend.common.api_handlers import BaseFieldModel
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


class VFolderItemField(BaseFieldModel):
    id: str
    name: str
    quota_scope_id: str
    host: str
    usage_mode: VFolderUsageMode
    created_at: str
    permission: VFolderPermissionField
    creator: str
    ownership_type: VFolderOwnershipTypeField
    user: str | None
    group: str | None
    cloneable: bool
    status: VFolderOperationStatusField
    is_owner: bool
    # Fields below are only available from the new /vfolders API;
    # the legacy /folders API does not include them.
    max_size: int = 0
    user_email: str = ""
    group_name: str = ""
    type: str = ""  # legacy
    max_files: int = 0
    cur_size: int = 0
