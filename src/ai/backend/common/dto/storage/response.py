from typing import List, Optional

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel


class VolumeMetadataResponse(BaseResponseModel):
    volume_id: str
    backend: str
    path: str
    fsprefix: Optional[str] = Field(default=None)
    capabilities: List[str]


class GetVolumeResponse(BaseResponseModel):
    volumes: List[VolumeMetadataResponse]


class QuotaScopeResponse(BaseResponseModel):
    used_bytes: Optional[int] = Field(default=0)
    limit_bytes: Optional[int] = Field(default=0)


class VFolderMetadataResponse(BaseResponseModel):
    mount_path: str
    file_count: int
    used_bytes: int
    capacity_bytes: int
    fs_used_bytes: int


class VFolderMountResponse(BaseResponseModel):
    mount_path: str


class VFolderUsageResponse(BaseResponseModel):
    file_count: int
    used_bytes: int


class VFolderUsedBytesResponse(BaseResponseModel):
    used_bytes: int


class VFolderFSUsageResponse(BaseResponseModel):
    capacity_bytes: int
    fs_used_bytes: int
