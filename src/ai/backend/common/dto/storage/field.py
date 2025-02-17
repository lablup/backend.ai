from typing import Optional

from pydantic import BaseModel, Field

from ...types import VolumeID


class VolumeMetaField(BaseModel):
    volume_id: VolumeID = Field(description="The unique identifier of the volume.")
    backend: str = Field(description="The backend type of the volume.")
    path: str = Field(description="The path of the volume.")
    fsprefix: Optional[str] = Field(description="The filesystem prefix of the volume.")
    capabilities: list[str] = Field(description="The capabilities of the volume.")


class VFolderMetaField(BaseModel):
    mount_path: str = Field(description="The mount path of the volume folder.")
    file_count: int = Field(description="The number of files in the volume folder.")
    used_bytes: int = Field(description="The number of bytes used in the volume folder.")
    capacity_bytes: int = Field(description="The total capacity of the volume folder.")
    fs_used_bytes: int = Field(description="The number of bytes used in the filesystem.")
