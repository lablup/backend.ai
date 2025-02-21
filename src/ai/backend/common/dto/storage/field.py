from typing import Optional

from pydantic import BaseModel, Field

from ...types import VolumeID


class VolumeMetaField(BaseModel):
    volume_id: VolumeID = Field(description="Used to uniquely identify a volume for operations.")
    backend: str = Field(description="Specifies the storage backend to determine handling methods.")
    path: str = Field(description="Defines the volume's location for access and management.")
    fsprefix: Optional[str] = Field(
        description="Indicates the filesystem prefix for path resolution."
    )
    capabilities: list[str] = Field(
        description="Lists allowed operations like read or write access."
    )


class VFolderMetaField(BaseModel):
    mount_path: str = Field(description="Defines where the vfolder is mounted for access.")
    file_count: int = Field(description="Tracks the number of files to monitor storage usage.")
    used_bytes: int = Field(description="Indicates the current storage usage for quota checks.")
    capacity_bytes: int = Field(description="Defines the maximum allowed storage capacity.")
    fs_used_bytes: int = Field(description="Includes metadata and overhead in filesystem usage.")
