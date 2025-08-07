from typing import Optional

from pydantic import Field

from ...api_handlers import BaseResponseModel
from .field import VFolderMetaField, VolumeMetaField


class GetVolumeResponse(BaseResponseModel):
    item: VolumeMetaField = Field(
        description="Provides metadata for a specific volume, used to manage and track storage operations."
    )


class GetVolumesResponse(BaseResponseModel):
    items: list[VolumeMetaField] = Field(
        description="Retrieves metadata for all available volumes, allowing for bulk management and monitoring."
    )


class QuotaScopeResponse(BaseResponseModel):
    used_bytes: Optional[int] = Field(
        default=0,
        description="Indicates the current usage within a quota scope, used for enforcing storage limits.",
    )
    limit_bytes: Optional[int] = Field(
        default=0,
        description="Defines the maximum allowed storage capacity within a quota scope, ensuring controlled resource allocation.",
    )


class VFolderMetadataResponse(BaseResponseModel):
    item: VFolderMetaField = Field(
        description="Provides metadata for a vfolder, used for storage tracking and access management."
    )


# S3 Storage API Response Models
class UploadObjectResponse(BaseResponseModel):
    pass


class PresignedUploadObjectResponse(BaseResponseModel):
    url: str
    fields: dict[str, str]


class PresignedDownloadObjectResponse(BaseResponseModel):
    url: str


class DeleteObjectResponse(BaseResponseModel):
    pass


class ObjectMetaResponse(BaseResponseModel):
    content_length: Optional[int]
    content_type: Optional[str]
    last_modified: Optional[str]
    etag: Optional[str]
    metadata: dict[str, str]
