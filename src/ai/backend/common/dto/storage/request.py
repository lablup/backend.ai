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


# HuggingFace API Request Models
class HuggingFaceListModelsReq(BaseRequestModel):
    """Request for listing HuggingFace models."""

    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of models to retrieve (1-100)",
    )
    search: Optional[str] = Field(
        default=None,
        description="Search query to filter models by name, description, or tags",
    )
    sort: str = Field(
        default="downloads",
        description="Sort criteria: 'downloads', 'likes', 'created', 'modified'",
    )


class HuggingFaceGetModelReq(BaseRequestModel):
    """Request for getting specific HuggingFace model details."""

    model_id: str = Field(
        ...,
        description="HuggingFace model ID (e.g., 'microsoft/DialoGPT-medium')",
    )


class HuggingFaceListFilesReq(BaseRequestModel):
    """Request for listing files in a HuggingFace model."""

    model_id: str = Field(
        ...,
        description="HuggingFace model ID to list files from",
    )


class HuggingFaceGetDownloadUrlReq(BaseRequestModel):
    """Request for getting download URL of a specific file in a HuggingFace model."""

    model_id: str = Field(
        ...,
        description="HuggingFace model ID containing the file",
    )
    filename: str = Field(
        ...,
        description="Name of the file to get download URL for",
    )


class HuggingFaceImportModelReq(BaseRequestModel):
    """Request for importing a HuggingFace model to storage."""

    model_id: str = Field(
        ...,
        description="HuggingFace model ID to import (e.g., 'microsoft/DialoGPT-medium')",
    )
    storage_name: str = Field(
        ...,
        description="Target storage name (e.g., MinIO storage name)",
    )
    bucket_name: str = Field(
        ...,
        description="Target bucket name within the storage",
    )
    rescan: bool = Field(
        default=True,
        description="Whether to rescan the model before importing",
    )


class HuggingFaceImportModelsBatchReq(BaseRequestModel):
    """Request for batch importing multiple HuggingFace models to storage."""

    model_ids: list[str] = Field(
        ...,
        min_length=1,
        description="List of HuggingFace model IDs to import",
    )
    storage_name: str = Field(
        ...,
        description="Target storage name (e.g., MinIO storage name)",
    )
    bucket_name: str = Field(
        ...,
        description="Target bucket name within the storage",
    )
    rescan: bool = Field(
        default=True,
        description="Whether to rescan the models before importing",
    )


class GetScanJobStatusReq(BaseRequestModel):
    """Request for getting the status of a HuggingFace scan job."""

    job_id: str = Field(
        ...,
        description="ID of the scan job to check status for",
    )
