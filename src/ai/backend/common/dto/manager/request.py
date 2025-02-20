import uuid
from typing import Optional

from pydantic import AliasChoices, Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.types import VFolderUsageMode

from ...typed_validators import VFolderName
from .field import VFolderPermissionField


class VFolderCreateReq(BaseRequestModel):
    name: VFolderName = Field(
        description="Name of the vfolder",
    )
    folder_host: Optional[str] = Field(
        validation_alias=AliasChoices("host", "folder_host"),
        default=None,
    )
    usage_mode: VFolderUsageMode = Field(default=VFolderUsageMode.GENERAL)
    permission: VFolderPermissionField = Field(default=VFolderPermissionField.READ_WRITE)
    unmanaged_path: Optional[str] = Field(
        validation_alias=AliasChoices("unmanaged_path", "unmanagedPath"),
        default=None,
    )
    group_id: Optional[uuid.UUID] = Field(
        validation_alias=AliasChoices("group", "groupId", "group_id"),
        default=None,
    )
    cloneable: bool = Field(
        default=False,
    )


class RenameVFolderReq(BaseRequestModel):
    new_name: VFolderName = Field(
        description="Name of the vfolder",
    )
