from typing import Optional

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.storage.field import VFolderMetaField, VolumeMetaField


class GetVolumeResponse(BaseResponseModel):
    item: VolumeMetaField


class GetVolumesResponse(BaseResponseModel):
    items: list[VolumeMetaField]


class QuotaScopeResponse(BaseResponseModel):
    used_bytes: Optional[int] = Field(default=0)
    limit_bytes: Optional[int] = Field(default=0)


class VFolderMetadataResponse(BaseResponseModel):
    item: VFolderMetaField
