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
class UploadResponse(BaseResponseModel):
    """Response for file upload operations."""

    success: bool
    key: str


class ErrorResponse(BaseResponseModel):
    """Generic error response."""

    error: str


class PresignedUploadResponse(BaseResponseModel):
    """Response containing presigned upload URL and form fields."""

    url: str
    fields: dict[str, str]


class PresignedDownloadResponse(BaseResponseModel):
    """Response containing presigned download URL."""

    url: str


class ObjectInfoResponse(BaseResponseModel):
    """Response containing S3 object metadata."""

    content_length: int | None = None
    content_type: str | None = None
    last_modified: str | None = None
    etag: str | None = None


class DeleteResponse(BaseResponseModel):
    """Response for object deletion operations."""

    success: bool


class S3ObjectInfo(BaseResponseModel):
    """Pydantic model for S3 object metadata information."""

    content_length: Optional[int] = None
    content_type: Optional[str] = None
    last_modified: Optional[str] = None
    etag: Optional[str] = None
    metadata: dict[str, str] = {}


class S3PresignedUploadData(BaseResponseModel):
    """Pydantic model for S3 presigned upload URL data."""

    url: str
    fields: dict[str, str]
    key: str
