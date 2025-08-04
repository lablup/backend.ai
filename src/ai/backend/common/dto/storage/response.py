import uuid
from typing import Optional

from pydantic import BaseModel, Field

from ai.backend.common.bgtask.types import BgtaskStatus
from ai.backend.common.data.storage.registries.types import FileInfo, ModelInfo

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

    models: list[ModelInfo] = Field(
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

    model: ModelInfo = Field(
        description="""
        Detailed information about the HuggingFace model.
        Includes all metadata, file listings, and download information.
        """,
    )


class HuggingFaceListFilesResponse(BaseResponseModel):
    """Response for listing files in a HuggingFace model."""

    files: list[FileInfo] = Field(
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

    models: list[ModelInfo] = Field(
        default_factory=list,
        description="""
        List of HuggingFace models scanned and retrieved.
        Each model includes comprehensive metadata and file information.
        """,
    )


class BgTaskProgress(BaseModel):
    current: int = Field(
        default=0,
        description="Current progress of the scan operation, expressed as a percentage.",
        examples=[0, 50, 100],
    )
    total: int = Field(
        default=0,
        description="Total number of items to be scanned, used to calculate progress.",
        examples=[100, 200, 0],
    )


class HuggingFaceScanJobStatusResponse(BaseResponseModel):
    """Response for HuggingFace scan job status."""

    task_id: uuid.UUID = Field(
        description="""
        Unique identifier for the scan job.
        Used to track and query the status of the scan operation.
        """,
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    status: BgtaskStatus = Field(
        description="""
        Current status of the job.
        Possible values: pending, running, completed, failed.
        """,
        examples=[status.value for status in BgtaskStatus],
    )
    progress: BgTaskProgress = Field(
        description="""
        Indicates how much of the scan operation has been completed.
        """,
        examples=[{"current": 50, "total": 100}, {"current": 100, "total": 100}],
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


class HuggingFaceImportResponse(BaseResponseModel):
    """Response for HuggingFace model import operation."""

    task_id: uuid.UUID = Field(
        description="""
        Unique identifier for the import job.
        Used to track the progress of the model import operation.
        """,
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )


class HuggingFaceImportBatchResponse(BaseResponseModel):
    """Response for HuggingFace batch model import operation."""

    task_id: uuid.UUID = Field(
        description="""
        Unique identifier for the batch import task.
        Used to track the progress of the batch model import operation.
        """,
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
