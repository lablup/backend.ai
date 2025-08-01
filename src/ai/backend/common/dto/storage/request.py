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
        description="""
        Maximum number of models to retrieve (1-100).
        Controls the number of models returned in a single request.
        """,
        examples=[10, 50, 100],
    )
    search: Optional[str] = Field(
        default=None,
        description="""
        Search query to filter models by name, description, or tags.
        Leave empty to retrieve all models without filtering.
        """,
        examples=[None, "GPT", "microsoft", "text-generation"],
    )
    sort: str = Field(
        default="downloads",
        description="""
        Sort criteria for ordering the results.
        Available options: 'downloads', 'likes', 'created', 'modified'.
        """,
        examples=["downloads", "likes", "created", "modified"],
    )


class HuggingFaceGetModelReq(BaseRequestModel):
    """Request for getting specific HuggingFace model details."""

    model_id: str = Field(
        description="""
        HuggingFace model ID to retrieve details for.
        Follows the format 'organization/model-name' or just 'model-name'.
        """,
        examples=["microsoft/DialoGPT-medium", "openai/gpt-2", "bert-base-uncased"],
    )


class HuggingFaceListFilesReq(BaseRequestModel):
    """Request for listing files in a HuggingFace model."""

    model_id: str = Field(
        description="""
        HuggingFace model ID to list files from.
        The model repository must be publicly accessible or accessible with provided credentials.
        """,
        examples=["microsoft/DialoGPT-medium", "openai/gpt-2"],
    )


class HuggingFaceGetDownloadUrlReq(BaseRequestModel):
    """Request for getting download URL of a specific file in a HuggingFace model."""

    model_id: str = Field(
        description="""
        HuggingFace model ID containing the file.
        Must be a valid and accessible model repository.
        """,
        examples=["microsoft/DialoGPT-medium", "openai/gpt-2"],
    )
    filename: str = Field(
        description="""
        Name of the file to get download URL for.
        Should be a valid file path within the model repository.
        """,
        examples=["config.json", "pytorch_model.bin", "tokenizer/vocab.txt"],
    )


class HuggingFaceImportModelReq(BaseRequestModel):
    """Request for importing a HuggingFace model to storage."""

    model_id: str = Field(
        description="""
        HuggingFace model ID to import.
        The model will be downloaded from HuggingFace Hub and stored in the specified storage.
        """,
        examples=["microsoft/DialoGPT-medium", "openai/gpt-2", "bert-base-uncased"],
    )
    storage_name: str = Field(
        description="""
        Target storage name where the model will be imported.
        Must be a configured and accessible storage backend.
        """,
        examples=["default-minio", "s3-storage", "local-storage"],
    )
    bucket_name: str = Field(
        description="""
        Target bucket name within the storage.
        The bucket must exist and be writable by the service.
        """,
        examples=["models", "huggingface-models", "ai-models"],
    )
    rescan: bool = Field(
        default=True,
        description="""
        Whether to rescan the model before importing.
        If true, the model metadata will be refreshed from HuggingFace Hub.
        """,
        examples=[True, False],
    )


class HuggingFaceImportModelsBatchReq(BaseRequestModel):
    """Request for batch importing multiple HuggingFace models to storage."""

    model_ids: list[str] = Field(
        min_length=1,
        description="""
        List of HuggingFace model IDs to import in batch.
        All models will be processed sequentially and imported to the same storage location.
        """,
        examples=[["microsoft/DialoGPT-medium", "openai/gpt-2"], ["bert-base-uncased"]],
    )
    storage_name: str = Field(
        description="""
        Target storage name where all models will be imported.
        Must be a configured and accessible storage backend.
        """,
        examples=["default-minio", "s3-storage", "local-storage"],
    )
    bucket_name: str = Field(
        description="""
        Target bucket name within the storage for all models.
        The bucket must exist and be writable by the service.
        """,
        examples=["models", "huggingface-models", "ai-models"],
    )
    rescan: bool = Field(
        default=True,
        description="""
        Whether to rescan all models before importing.
        If true, all model metadata will be refreshed from HuggingFace Hub.
        """,
        examples=[True, False],
    )


class GetScanJobStatusReq(BaseRequestModel):
    """Request for getting the status of a HuggingFace scan job."""

    job_id: str = Field(
        description="""
        ID of the scan job to check status for.
        This ID is returned when starting a scan operation.
        """,
        examples=["550e8400-e29b-41d4-a716-446655440000", "123e4567-e89b-12d3-a456-426614174000"],
    )
