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

    content_length: Optional[int] = None
    content_type: Optional[str] = None
    last_modified: Optional[str] = None
    etag: Optional[str] = None


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


# HuggingFace API Response Models


class HuggingFaceListModelsResponse(BaseResponseModel):
    """Response for listing HuggingFace models."""

    models: list[HuggingFaceModelInfo] = Field(
        default_factory=list,
        description="""
        List of HuggingFace models with metadata.
        Each model includes comprehensive information about the model and its files.
        """,
    )
    total_count: int = Field(
        default=0,
        description="""
        Total number of models returned in this response.
        May be less than the requested limit if fewer models are available.
        """,
        examples=[10, 50, 0],
    )


class HuggingFaceGetModelResponse(BaseResponseModel):
    """Response for getting specific HuggingFace model details."""

    model: HuggingFaceModelInfo = Field(
        description="""
        Detailed information about the HuggingFace model.
        Includes all metadata, file listings, and download information.
        """,
    )


class HuggingFaceListFilesResponse(BaseResponseModel):
    """Response for listing files in a HuggingFace model."""

    files: list[HuggingFaceFileData] = Field(
        default_factory=list,
        description="""
        List of files in the HuggingFace model repository.
        Includes all model files, configuration files, and documentation.
        """,
    )
    model_id: str = Field(
        description="""
        HuggingFace model ID that the files belong to.
        Used to identify which model these files are associated with.
        """,
        examples=["microsoft/DialoGPT-medium", "openai/gpt-2"],
    )


class HuggingFaceGetDownloadUrlResponse(BaseResponseModel):
    """Response for getting download URL of a specific file."""

    download_url: str = Field(
        description="""
        Direct HTTP URL for downloading the file.
        This URL can be used to download the file directly from HuggingFace Hub.
        """,
        examples=["https://huggingface.co/microsoft/DialoGPT-medium/resolve/main/config.json"],
    )
    model_id: str = Field(
        description="""
        HuggingFace model ID containing the file.
        Identifies the model repository that contains this file.
        """,
        examples=["microsoft/DialoGPT-medium", "openai/gpt-2"],
    )
    filename: str = Field(
        description="""
        Name of the file within the model repository.
        Relative path from the repository root to the file.
        """,
        examples=["config.json", "pytorch_model.bin", "tokenizer/vocab.txt"],
    )


class HuggingFaceScanResponse(BaseResponseModel):
    """Response for HuggingFace scan operation."""

    models: list[HuggingFaceModelInfo] = Field(
        default_factory=list,
        description="""
        List of scanned HuggingFace models.
        Contains all models found during the scan operation with their metadata.
        """,
    )
    total_count: int = Field(
        default=0,
        description="""
        Total number of models scanned.
        Indicates how many models were successfully processed during the scan.
        """,
        examples=[10, 50, 0],
    )
    # TODO: Optional 제거.
    job_id: Optional[uuid.UUID] = Field(
        default=None,
        description="""
        Job ID for tracking scan progress.
        Used to monitor the status of long-running scan operations.
        """,
        examples=["550e8400-e29b-41d4-a716-446655440000", None],
    )


class HuggingFaceScanJobStatusResponse(BaseResponseModel):
    """Response for HuggingFace scan job status."""

    job_id: uuid.UUID = Field(
        description="""
        Unique identifier for the scan job.
        Used to track and query the status of the scan operation.
        """,
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    status: str = Field(
        description="""
        Current status of the job.
        Possible values: pending, running, completed, failed.
        """,
        examples=["pending", "running", "completed", "failed"],
    )
    progress: int = Field(
        default=0,
        ge=0,
        le=100,
        description="""
        Progress percentage (0-100).
        Indicates how much of the scan operation has been completed.
        """,
        examples=[0, 50, 100],
    )
    message: str = Field(
        default="",
        description="""
        Status message or error description.
        Provides additional information about the current job status.
        """,
        examples=[
            "Scanning in progress",
            "Scan completed successfully",
            "Error: Model not found",
        ],
    )
    started_at: Optional[str] = Field(
        default=None,
        description="""
        ISO timestamp when the job started.
        Null if the job hasn't started yet.
        """,
        examples=["2023-12-01T10:00:00Z", None],
    )
    completed_at: Optional[str] = Field(
        default=None,
        description="""
        ISO timestamp when the job completed.
        Null if the job is still running or hasn't started.
        """,
        examples=["2023-12-01T10:05:00Z", None],
    )


class HuggingFaceImportResponse(BaseResponseModel):
    """Response for HuggingFace model import operation."""

    job_id: uuid.UUID = Field(
        description="""
        Unique identifier for the import job.
        Used to track the progress of the model import operation.
        """,
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    status: str = Field(
        description="""
        Current status of the import job.
        Possible values: started, running, completed, failed.
        """,
        examples=["started", "running", "completed", "failed"],
    )
    model_id: str = Field(
        description="""
        HuggingFace model ID being imported.
        The model that is currently being downloaded and stored.
        """,
        examples=["microsoft/DialoGPT-medium", "openai/gpt-2"],
    )
    storage_name: str = Field(
        description="""
        Target storage name where the model is being imported.
        The configured storage backend receiving the model files.
        """,
        examples=["default-minio", "s3-storage"],
    )
    bucket_name: str = Field(
        description="""
        Target bucket name within the storage.
        The specific bucket where model files are being stored.
        """,
        examples=["models", "huggingface-models"],
    )
    message: str = Field(
        default="Import job started successfully",
        description="""
        Status message providing additional information about the import job.
        Contains success confirmations or error details.
        """,
        examples=[
            "Import job started successfully",
            "Import completed",
            "Error: Storage not accessible",
        ],
    )


class HuggingFaceImportBatchResponse(BaseResponseModel):
    """Response for HuggingFace batch model import operation."""

    job_id: uuid.UUID = Field(
        description="""
        Unique identifier for the batch import job.
        Used to track the progress of the batch model import operation.
        """,
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    status: str = Field(
        description="""
        Current status of the batch import job.
        Possible values: started, running, completed, failed.
        """,
        examples=["started", "running", "completed", "failed"],
    )
    model_ids: list[str] = Field(
        description="""
        List of HuggingFace model IDs being imported in batch.
        All models in this list will be processed and imported.
        """,
        examples=[["microsoft/DialoGPT-medium", "openai/gpt-2"], ["bert-base-uncased"]],
    )
    storage_name: str = Field(
        description="""
        Target storage name where all models are being imported.
        The configured storage backend receiving all model files.
        """,
        examples=["default-minio", "s3-storage"],
    )
    bucket_name: str = Field(
        description="""
        Target bucket name within the storage for all models.
        The specific bucket where all model files are being stored.
        """,
        examples=["models", "huggingface-models"],
    )
    total_models: int = Field(
        description="""
        Total number of models to import in this batch.
        Indicates the scope of the batch import operation.
        """,
        examples=[2, 5, 10],
    )
    message: str = Field(
        default="Batch import job started successfully",
        description="""
        Status message providing additional information about the batch import job.
        Contains success confirmations or error details for the batch operation.
        """,
        examples=[
            "Batch import job started successfully",
            "Batch import completed",
            "Error: Some models failed to import",
        ],
    )
