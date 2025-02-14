from typing import Optional

from pydantic import BaseModel

from ...types import VolumeID


class VolumeMetaField(BaseModel):
    volume_id: VolumeID
    backend: str
    path: str
    fsprefix: Optional[str]
    capabilities: list[str]


class VFolderMetaField(BaseModel):
    mount_path: str
    file_count: int
    used_bytes: int
    capacity_bytes: int
    fs_used_bytes: int
