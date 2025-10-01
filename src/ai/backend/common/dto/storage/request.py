from typing import Optional

from pydantic import Field

from ...api_handlers import BaseRequestModel
from ...data.storage.registries.types import ModelSortKey, ModelTarget
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


class DownloadObjectReq(BaseRequestModel):
    """
    Data model for file download requests from object storage.
    """

    key: str = Field(description="The object key (path) within the bucket to upload the file to.")


class PresignedUploadObjectReq(BaseRequestModel):
    """
    Data model for generating presigned upload URLs for object storage operations.
    This is used to specify the target bucket, key, and optional parameters for the presigned URL.
    """

    key: str = Field(description="The object key (path) within the bucket to upload the file to.")


class PresignedDownloadObjectReq(BaseRequestModel):
    """
    Data model for generating presigned download URLs for object storage operations.
    """

    key: str = Field(
        description="The object key (path) within the bucket to download the file from."
    )
    expiration: Optional[int] = Field(default=None, description="Token expiration time in seconds")


class GetObjectMetaReq(BaseRequestModel):
    """
    Data model for retrieving metadata of a file in object storage.
    This is used to specify the target bucket and key for the file metadata retrieval.
    """

    key: str = Field(
        description="The object key (path) within the bucket to retrieve metadata for."
    )


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
        ge=1,
        description="""
        Maximum number of models to retrieve.
        Controls the number of models returned in a single request.
        """,
        examples=[10, 50, 100],
    )
    order: ModelSortKey = Field(
        description="""
        Sort criteria for ordering the results.
        Available options: 'downloads', 'likes', 'created', 'modified'.
        """,
        examples=["downloads", "likes", "created", "modified"],
    )
    search: Optional[str] = Field(
        default=None,
        description="""
        Search query to filter models by name, description, or tags.
        Leave empty to retrieve all models without filtering.
        """,
        examples=[None, "GPT", "microsoft", "text-generation"],
    )


class HuggingFaceScanModelsSyncReq(BaseRequestModel):
    """Request for scanning HuggingFace models."""

    registry_name: str = Field(
        description="""
        Name of the HuggingFace registry to scan.
        This should match the configured registry name in the system.
        """,
        examples=["huggingface", "my-huggingface-registry"],
    )
    limit: int = Field(
        ge=1,
        description="""
        Maximum number of models to retrieve.
        Controls the number of models returned in a single request.
        """,
        examples=[10, 50, 100],
    )
    order: ModelSortKey = Field(
        description="""
        Sort criteria for ordering the results.
        Available options: 'downloads', 'likes', 'created', 'modified'.
        """,
        examples=["downloads", "likes", "created", "modified"],
    )
    search: Optional[str] = Field(
        default=None,
        description="""
        Search query to filter models by name, description, or tags.
        Leave empty to retrieve all models without filtering.
        """,
        examples=[None, "GPT", "microsoft", "text-generation"],
    )


class HuggingFaceRetrieveModelsReq(BaseRequestModel):
    """Request for retrieve HuggingFace models."""

    registry_name: str = Field(
        description="""
        Name of the HuggingFace registry to scan.
        This should match the configured registry name in the system.
        """,
        examples=["huggingface", "my-huggingface-registry"],
    )
    models: list[ModelTarget] = Field(
        description="""
        List of model targets to retrieve from the HuggingFace registry.
        Each target must specify the model ID and optional revision.
        """,
        examples=[
            {"model_id": "microsoft/DialoGPT-medium", "revision": "main"},
        ],
    )


class HuggingFaceRetrieveModelReqPathParam(BaseRequestModel):
    """
    Path parameters for retrieving a specific HuggingFace model.
    """

    model_id: str = Field(description="The model to scan from the registry.")


class HuggingFaceRetrieveModelReqQueryParam(BaseRequestModel):
    """
    Query parameters for retrieving a specific HuggingFace model.
    """

    registry_name: str = Field(
        description="""
        Name of the HuggingFace registry to scan.
        This should match the configured registry name in the system.
        """,
        examples=["huggingface", "my-huggingface-registry"],
    )
    revision: str = Field(description="The model revision to scan from the registry.")


class HuggingFaceImportModelsReq(BaseRequestModel):
    """Request for batch importing multiple HuggingFace models to storage."""

    models: list[ModelTarget] = Field(
        description="""
        List of models to import from HuggingFace.
        Each model must specify the model ID and optional revision.
        """,
        examples=[
            [
                {"model_id": "microsoft/DialoGPT-medium", "revision": "main"},
                {"model_id": "openai/gpt-2", "revision": "v1.0"},
            ]
        ],
    )
    registry_name: str = Field(
        description="""
        Name of the HuggingFace registry to import from.
        This should match the configured registry name in the system.
        """,
        examples=["huggingface", "my-huggingface"],
    )
    storage_name: str = Field(
        description="""
        Target storage name where all models will be imported.
        Must be a configured and accessible storage backend.
        """,
        examples=["default-minio", "s3-storage", "local-storage"],
    )


class ReservoirImportModelsReq(BaseRequestModel):
    """Request for batch importing multiple models to storage."""

    models: list[ModelTarget] = Field(
        description="""
        List of models to import.
        Each model must specify the model ID and optional revision.
        """,
        examples=[
            [
                {"model_id": "microsoft/DialoGPT-medium", "revision": "main"},
                {"model_id": "openai/gpt-2", "revision": "v1.0"},
            ]
        ],
    )
    registry_name: str = Field(
        description="""
        Name of the Reservoir registry to import from.
        This should match the configured registry name in the system.
        """,
        examples=["reservoir", "my-reservoir"],
    )
    storage_name: str = Field(
        description="""
        Target storage name where all models will be imported.
        Must be a configured and accessible storage backend.
        """,
        examples=["default-minio", "s3-storage", "local-storage"],
    )


class DeleteObjectReq(BaseRequestModel):
    """
    Data model for file deletion requests from object storage.
    """

    key: str = Field(description="The object key (path) within the bucket to delete the file from.")


# VFS Storage Request DTOs
class VFSStorageAPIPathParams(BaseRequestModel):
    """Path parameters for VFS storage API endpoints."""

    storage_name: str = Field(
        description="The name of the VFS storage configuration to use for the operation."
    )


class VFSUploadFileReq(BaseRequestModel):
    """
    Data model for file upload requests to VFS storage.
    This is used to specify the target filepath and options for the file upload.
    """

    filepath: str = Field(description="The file path within VFS storage to upload the file to.")
    content_type: Optional[str] = Field(
        default=None, description="MIME type of the file being uploaded (optional for VFS)."
    )


class VFSDownloadFileReq(BaseRequestModel):
    """
    Data model for file download requests from VFS storage.
    """

    filepath: str = Field(description="The file path within VFS storage to download the file from.")


class VFSGetFileMetaReq(BaseRequestModel):
    """
    Data model for retrieving metadata of a file in VFS storage.
    """

    filepath: str = Field(description="The file path within VFS storage to retrieve metadata for.")


class VFSDeleteFileReq(BaseRequestModel):
    """
    Data model for deleting files from VFS storage.
    """

    filepath: str = Field(description="The file path within VFS storage to delete.")
