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
