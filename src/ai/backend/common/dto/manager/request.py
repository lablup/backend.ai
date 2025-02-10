import uuid
from typing import Optional

from pydantic import AliasChoices, BaseModel, Field

from ai.backend.common import typed_validators as tv
from ai.backend.common.dto.manager.dto import VFolderPermissionDTO
from ai.backend.common.types import VFolderUsageMode


class VFolderCreateReq(BaseModel):
    name: tv.VFolderName = Field(
        description="Name of the vfolder",
    )
    folder_host: Optional[str] = Field(
        validation_alias=AliasChoices("host", "folder_host"),
        default=None,
    )
    usage_mode: VFolderUsageMode = Field(default=VFolderUsageMode.GENERAL)
    permission: VFolderPermissionDTO = Field(default=VFolderPermissionDTO.READ_WRITE)
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


class RenameVFolderReq(BaseModel):
    new_name: tv.VFolderName = Field(
        description="Name of the vfolder",
    )
