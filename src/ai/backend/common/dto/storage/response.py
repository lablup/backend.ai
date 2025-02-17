from typing import Optional

from pydantic import Field

from ...api_handlers import BaseResponseModel
from .field import VFolderMetaField, VolumeMetaField


class GetVolumeResponse(BaseResponseModel):
    item: VolumeMetaField = Field(description="The volume metadata.")


class GetVolumesResponse(BaseResponseModel):
    items: list[VolumeMetaField] = Field(description="The list of volume metadata.")


class QuotaScopeResponse(BaseResponseModel):
    used_bytes: Optional[int] = Field(
        default=0, description="The number of bytes used in the quota scope."
    )
    limit_bytes: Optional[int] = Field(
        default=0, description="The total capacity of the quota scope."
    )


class VFolderMetadataResponse(BaseResponseModel):
    item: VFolderMetaField = Field(description="The volume folder metadata.")
