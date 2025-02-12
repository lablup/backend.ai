from typing import List, Optional

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.types import BinarySize


class VolumeMetadataResponse(BaseResponseModel):
    volume_id: str = Field(..., description="A unique identifier for the volume.")
    backend: str = Field(..., description="The backend name.")
    path: str = Field(..., description="The path to the volume.")
    fsprefix: Optional[str] = Field(default=None, description="The prefix for the filesystem.")
    capabilities: List[str] = Field(..., description="The capabilities of the volume.")


class GetVolumeResponse(BaseResponseModel):
    volumes: List[VolumeMetadataResponse] = Field(..., description="The list of volumes.")


class QuotaScopeResponse(BaseResponseModel):
    used_bytes: Optional[int] = Field(
        default=0, description="The number of bytes currently used within the quota scope."
    )
    limit_bytes: Optional[int] = Field(
        default=0,
        description="The maximum number of bytes that can be used within the quota scope.",
    )


class VFolderMetadataResponse(BaseResponseModel):
    mount_path: str = Field(..., description="The path where the virtual folder is mounted.")
    file_count: int = Field(..., description="The number of files in the virtual folder.")
    capacity_bytes: int = Field(
        ..., description="The total capacity in bytes of the virtual folder."
    )
    used_bytes: BinarySize = Field(
        ..., description="The used capacity in bytes of the virtual folder."
    )
