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


class ObjectStorageAPIPathParams(BaseRequestModel):
    storage_name: str = Field(
        description="The name of the storage configuration to use for the operation."
    )
    bucket_name: str = Field(description="The name of the S3 bucket to operate on.")


class UploadObjectReq(BaseRequestModel):
    """
    Data model for file upload requests to object storage.
    This is used to specify the target bucket and key for the file upload.
    """

    key: str = Field(description="The object key (path) within the bucket to upload the file to.")
    content_type: Optional[str] = Field(
        default=None, description="MIME type of the file being uploaded."
    )
    content_length: Optional[int] = Field(
        default=None, ge=0, description="Total content length of the file being uploaded."
    )


class DownloadObjectReq(BaseRequestModel):
    """
    Data model for file download requests from object storage.
    """

    key: str = Field(description="The object key (path) within the bucket to upload the file to.")


class PresignedUploadObjectReq(BaseRequestModel):
    """
    Data model for generating presigned upload URLs for object storage operations.
    This is used to specify the target bucket, key, and optional parameters for the presigned
    """

    key: str = Field(description="The object key (path) within the bucket to upload the file to.")
    content_type: Optional[str] = Field(
        default=None, description="MIME type of the file being uploaded."
    )
    expiration: Optional[int] = Field(
        default=None, gt=0, description="Token expiration time in seconds"
    )
    min_size: Optional[int] = Field(
        default=None, ge=0, description="Minimum allowed size in bytes for upload operations"
    )
    max_size: Optional[int] = Field(
        default=None, gt=0, description="Maximum allowed size in bytes for upload operations"
    )


class PresignedDownloadObjectReq(BaseRequestModel):
    """
    Data model for generating presigned download URLs for object storage operations.
    """

    key: str = Field(
        description="The object key (path) within the bucket to download the file from."
    )


class GetObjectMetaReq(BaseRequestModel):
    """
    Data model for retrieving metadata of a file in object storage.
    This is used to specify the target bucket and key for the file metadata retrieval.
    """

    key: str = Field(
        description="The object key (path) within the bucket to retrieve metadata for."
    )


class DeleteObjectReq(BaseRequestModel):
    """
    Data model for deleting a file in object storage.
    This is used to specify the target bucket and key for the file deletion.
    """

    key: str = Field(description="The object key (path) within the bucket to delete the file from.")


class UploadDirectoryReq(BaseRequestModel):
    """
    Data model for directory upload requests to object storage.
    This is used to specify the target bucket and directory prefix for multiple file uploads.
    """

    prefix: str = Field(
        description="The directory prefix (path) within the bucket to upload files to."
    )
    overwrite: bool = Field(
        default=False, description="Whether to overwrite existing files with the same keys."
    )


class DownloadDirectoryReq(BaseRequestModel):
    """
    Data model for directory download requests from object storage.
    This is used to specify the directory prefix to download from the bucket.
    """

    prefix: str = Field(
        description="The directory prefix (path) within the bucket to download files from."
    )
    recursive: bool = Field(
        default=True, description="Whether to recursively download all files under the prefix."
    )


class DeleteDirectoryReq(BaseRequestModel):
    """
    Data model for directory deletion requests in object storage.
    This is used to specify the directory prefix to delete from the bucket.
    """

    prefix: str = Field(
        description="The directory prefix (path) within the bucket to delete files from."
    )
    recursive: bool = Field(
        default=True, description="Whether to recursively delete all files under the prefix."
    )


# HuggingFace API Request Models
class HuggingFaceScanModelsReq(BaseRequestModel):
    """Request for scanning HuggingFace models."""

    registry_name: str = Field(
        description="""
        Name of the HuggingFace registry to scan.
        This should match the configured registry name in the system.
        """,
        examples=["huggingface", "my-huggingface-registry"],
    )
    limit: int = Field(
        default=10,
        ge=1,
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
    order: str = Field(
        default="downloads",
        description="""
        Sort criteria for ordering the results.
        Available options: 'downloads', 'likes', 'created', 'modified'.
        """,
        examples=["downloads", "likes", "created", "modified"],
    )


class HuggingFaceImportModelReq(BaseRequestModel):
    """Request for importing a HuggingFace model to storage."""

    registry_name: str = Field(
        description="""
        Name of the HuggingFace registry to import from.
        This should match the configured registry name in the system.
        """,
        examples=["huggingface", "my-huggingface-registry"],
    )
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


class HuggingFaceImportModelsBatchReq(BaseRequestModel):
    """Request for batch importing multiple HuggingFace models to storage."""

    registry_name: str = Field(
        description="""
        Name of the HuggingFace registry to import from.
        This should match the configured registry name in the system.
        """,
        examples=["huggingface", "my-huggingface-registry"],
    )
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


class HuggingFaceImportTaskStatusReq(BaseRequestModel):
    """Request for getting the status of a HuggingFace scan job."""

    task_id: str = Field(
        description="""
        ID of the import job to check status for.
        This ID is returned when starting a scan operation.
        """,
        examples=["550e8400-e29b-41d4-a716-446655440000", "123e4567-e89b-12d3-a456-426614174000"],
    )
