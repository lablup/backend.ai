import uuid
from typing import Optional

from pydantic import Field

from ai.backend.common.data.storage.registries.types import (
    HuggingFaceFileData,
    HuggingFaceModelInfo,
)

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


class S3PresignedUploadData(BaseResponseModel):
    """Pydantic model for S3 presigned upload URL data."""

    url: str
    fields: dict[str, str]
    key: str


# HuggingFace API Response Models


class HuggingFaceListModelsResponse(BaseResponseModel):
    """Response for listing HuggingFace models."""

    models: list[HuggingFaceModelInfo] = Field(
        default_factory=list,
        description="List of HuggingFace models with metadata",
    )
    total_count: int = Field(
        default=0,
        description="Total number of models returned",
    )


class HuggingFaceGetModelResponse(BaseResponseModel):
    """Response for getting specific HuggingFace model details."""

    model: HuggingFaceModelInfo = Field(
        ...,
        description="Detailed information about the HuggingFace model",
    )


class HuggingFaceListFilesResponse(BaseResponseModel):
    """Response for listing files in a HuggingFace model."""

    files: list[HuggingFaceFileData] = Field(
        default_factory=list,
        description="List of files in the HuggingFace model repository",
    )
    model_id: str = Field(
        ...,
        description="HuggingFace model ID that the files belong to",
    )


class HuggingFaceGetDownloadUrlResponse(BaseResponseModel):
    """Response for getting download URL of a specific file."""

    download_url: str = Field(
        ...,
        description="Direct HTTP URL for downloading the file",
    )
    model_id: str = Field(
        ...,
        description="HuggingFace model ID containing the file",
    )
    filename: str = Field(
        ...,
        description="Name of the file",
    )


class HuggingFaceScanResponse(BaseResponseModel):
    """Response for HuggingFace scan operation."""

    models: list[HuggingFaceModelInfo] = Field(
        default_factory=list,
        description="List of scanned HuggingFace models",
    )
    total_count: int = Field(
        default=0,
        description="Total number of models scanned",
    )
    # TODO: Optional 제거.
    job_id: Optional[uuid.UUID] = Field(
        default=None,
        description="Job ID for tracking scan progress",
    )


class HuggingFaceScanJobStatusResponse(BaseResponseModel):
    """Response for HuggingFace scan job status."""

    job_id: uuid.UUID = Field(
        ...,
        description="Unique identifier for the scan job",
    )
    status: str = Field(
        ...,
        description="Current status of the job (pending, running, completed, failed)",
    )
    progress: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Progress percentage (0-100)",
    )
    message: str = Field(
        default="",
        description="Status message or error description",
    )
    started_at: Optional[str] = Field(
        default=None,
        description="ISO timestamp when the job started",
    )
    completed_at: Optional[str] = Field(
        default=None,
        description="ISO timestamp when the job completed",
    )


class HuggingFaceImportResponse(BaseResponseModel):
    """Response for HuggingFace model import operation."""

    job_id: uuid.UUID = Field(
        ...,
        description="Unique identifier for the import job",
    )
    status: str = Field(
        ...,
        description="Current status of the import job (started, running, completed, failed)",
    )
    model_id: str = Field(
        ...,
        description="HuggingFace model ID being imported",
    )
    storage_name: str = Field(
        ...,
        description="Target storage name",
    )
    bucket_name: str = Field(
        ...,
        description="Target bucket name",
    )
    message: str = Field(
        default="Import job started successfully",
        description="Status message",
    )


class HuggingFaceImportBatchResponse(BaseResponseModel):
    """Response for HuggingFace batch model import operation."""

    job_id: uuid.UUID = Field(
        ...,
        description="Unique identifier for the batch import job",
    )
    status: str = Field(
        ...,
        description="Current status of the batch import job (started, running, completed, failed)",
    )
    model_ids: list[str] = Field(
        ...,
        description="List of HuggingFace model IDs being imported",
    )
    storage_name: str = Field(
        ...,
        description="Target storage name",
    )
    bucket_name: str = Field(
        ...,
        description="Target bucket name",
    )
    total_models: int = Field(
        ...,
        description="Total number of models to import",
    )
    message: str = Field(
        default="Batch import job started successfully",
        description="Status message",
    )
