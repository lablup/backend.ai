import enum
from typing import Optional

from pydantic import Field

from ...api_handlers import BaseRequestModel
from ...types import QuotaConfig, VFolderID


class QuotaScopeReq(BaseRequestModel):
    options: Optional[QuotaConfig] = Field(
        default=None,
        description="The options for the quota scope.",
    )


class GetVFolderMetaReq(BaseRequestModel):
    subpath: str = Field(
        description="The subpath of the virtual folder.",
    )


class CloneVFolderReq(BaseRequestModel):
    dst_vfolder_id: VFolderID = Field(
        description="The destination virtual folder ID.",
        alias="dst_vfid",
    )


class ObjectStorageOperationType(enum.StrEnum):
    """Enumeration of supported object storage operations."""

    UPLOAD = "upload"
    DOWNLOAD = "download"
    INFO = "info"
    DELETE = "delete"
    PRESIGNED_UPLOAD = "presigned_upload"
    PRESIGNED_DOWNLOAD = "presigned_download"


class ObjectStorageTokenData(BaseRequestModel):
    """
    JWT token data for authenticated object storage operations.

    This token contains all the necessary information to perform
    secure operations on object storage systems like S3.
    """

    op: ObjectStorageOperationType = Field(description="The type of storage operation to perform")
    bucket: str = Field(description="The name of the storage bucket to operate on")
    key: str = Field(description="The object key (path) within the bucket")
    expiration: Optional[int] = Field(
        default=None, gt=0, le=604800, description="Token expiration time in seconds (max 7 days)"
    )
    content_type: Optional[str] = Field(
        default=None, description="MIME type of the object for upload operations"
    )
    min_size: Optional[int] = Field(
        default=None, ge=0, description="Minimum allowed size in bytes for upload operations"
    )
    max_size: Optional[int] = Field(
        default=None, gt=0, description="Maximum allowed size in bytes for upload operations"
    )
    filename: Optional[str] = Field(
        default=None, description="Original filename for download operations"
    )
