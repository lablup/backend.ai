import uuid
from collections.abc import Mapping
from datetime import datetime
from enum import StrEnum
from pathlib import PurePosixPath

from pydantic import BaseModel, ConfigDict, Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.data.storage.registries.types import ModelSortKey, ModelTarget
from ai.backend.common.data.storage.types import (
    ArtifactStorageImportStep,
    ArtifactStorageTarget,
)
from ai.backend.common.type_adapters import VFolderIDField
from ai.backend.common.types import QuotaConfig


class QuotaScopeReq(BaseRequestModel):
    options: QuotaConfig | None = Field(
        default=None,
        description="The options for the quota scope.",
    )


class GetVFolderMetaReq(BaseRequestModel):
    subpath: str = Field(
        description="The subpath of the virtual folder.",
    )


class CloneVFolderReq(BaseRequestModel):
    dst_vfolder_id: VFolderIDField = Field(
        description="The destination virtual folder ID.",
        alias="dst_vfid",
    )


class FileDeleteAsyncRequest(BaseRequestModel):
    """
    Request for asynchronous file deletion within a virtual folder.

    This request initiates a background task to delete files/directories,
    returning immediately with a task ID that can be used to track progress.
    """

    volume: str = Field(
        description="""
        Volume name where the vfolder is located.
        This identifies the storage backend (e.g., 'local', 'ceph', 'nfs')
        that contains the virtual folder. The volume name must match one of
        the configured volumes in the storage proxy.
        """,
        examples=["local", "ceph-volume-1", "nfs-shared"],
    )
    vfid: VFolderIDField = Field(
        description="""
        Virtual folder ID containing the files to delete.
        This is a composite identifier consisting of quota_scope_id and folder_id,
        uniquely identifying the vfolder within the storage system.
        Format: "{quota_scope_id}/{folder_id}" or just "{folder_id}" for legacy vfolders.
        """,
        examples=["user:550e8400-e29b-41d4-a716-446655440000/a1b2c3d4", "a1b2c3d4"],
    )
    relpaths: list[PurePosixPath] = Field(
        description="""
        List of relative paths of files/directories to delete within the vfolder.
        All paths must be relative to the vfolder root and use POSIX path format.
        Use forward slashes (/) as path separators regardless of the host OS.
        Example: ["data/logs/old.log", "temp/cache", "reports/2024/january.pdf"]
        """,
        examples=[["data/file.txt"], ["logs/old", "cache/temp.dat"]],
    )
    recursive: bool = Field(
        default=False,
        description="""
        Whether to delete directories recursively.
        - If True: Directories and all their contents will be deleted (like 'rm -rf')
        - If False: Only files and empty directories can be deleted
        Defaults to False for safety. Set to True when deleting non-empty directories.
        """,
        examples=[False, True],
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
    expiration: int | None = Field(default=None, description="Token expiration time in seconds")


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
    search: str | None = Field(
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
    search: str | None = Field(
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


class StorageMappingResolverData(BaseRequestModel):
    """
    Storage target configuration for model import.

    Provides two ways to specify storage targets:
    - storage_step_mappings: Simple string-based storage names (resolved via storage pool)
    - storage_step_target_mappings: Structured targets (NamedStorageTarget or VFolderStorageTarget)

    Both can be provided; they will be merged with storage_step_target_mappings taking precedence.
    """

    storage_step_mappings: Mapping[ArtifactStorageImportStep, str] | None = Field(
        default=None,
        description="""
        Deprecated.
        Mapping of import steps to storage names (string-based).
        These will be resolved via storage pool lookup.
        """,
        examples=[
            {"download": "fast-storage", "archive": "long-term-storage"},
        ],
    )

    storage_step_target_mappings: (
        Mapping[ArtifactStorageImportStep, ArtifactStorageTarget] | None
    ) = Field(
        default=None,
        description="""
        Mapping of import steps to structured storage targets.
        Each target can be either a NamedStorageTarget or a VFolderStorageTarget object.
        Takes precedence over storage_step_mappings for the same step.
        """,
        examples=[
            {
                "download": {"storage_name": "fast-storage"},
                "archive": {"storage_name": "long-term-storage"},
            },
            {
                "download": {"vfolder_id": "xxx", "volume_name": "volume1"},
                "archive": {"vfolder_id": "xxx", "volume_name": "volume1"},
            },
        ],
    )


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
    storage_step_mappings: Mapping[ArtifactStorageImportStep, str] | None = Field(
        default=None,
        description="""
        Deprecated. Use storage_step_target_mappings instead.
        Mapping of import steps to storage names (string-based).
        These will be resolved via storage pool lookup.
        """,
        examples=[
            {"download": "fast-storage", "archive": "long-term-storage"},
        ],
    )
    storage_step_target_mappings: (
        Mapping[ArtifactStorageImportStep, ArtifactStorageTarget] | None
    ) = Field(
        default=None,
        description="""
        Mapping of import steps to structured storage targets.
        Each target can be either a NamedStorageTarget or a VFolderStorageTarget object.
        Takes precedence over storage_step_mappings for the same step.
        """,
        examples=[
            {
                "download": {"storage_name": "fast-storage"},
                "archive": {"storage_name": "long-term-storage"},
            },
            {
                "download": {"vfolder_id": "xxx", "volume_name": "volume1"},
                "archive": {"vfolder_id": "xxx", "volume_name": "volume1"},
            },
        ],
    )
    storage_prefix: str | None = Field(
        default=None,
        description="""
        Custom prefix path for storing imported artifacts.
        - If not specified (None): Uses the artifact-type-specific default path.
          For models, the default is `{model_id}/{revision}`
          (e.g., "microsoft/DialoGPT-medium/main/").
          Default paths for other artifact types (PACKAGE, IMAGE) are not yet defined.
        - If set to "/": Files will be stored at the root without any prefix.
        - If set to a custom value (e.g., "my-models"): Files will be stored under
          the specified custom prefix.
        """,
        examples=["my-models", "custom/path", "/"],
    )


class HuggingFaceGetCommitHashReqPathParam(BaseRequestModel):
    """
    Path parameters for getting HuggingFace model commit hash.
    """

    model_id: str = Field(description="The model to get commit hash for.")


class HuggingFaceGetCommitHashReqQueryParam(BaseRequestModel):
    """
    Query parameters for getting HuggingFace model commit hash.
    """

    registry_name: str = Field(
        description="""
        Name of the HuggingFace registry.
        This should match the configured registry name in the system.
        """,
        examples=["huggingface", "my-huggingface-registry"],
    )
    revision: str | None = Field(
        default=None,
        description="The revision (branch/tag) of the model.",
        examples=["main", "v1.0"],
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
    storage_step_mappings: Mapping[ArtifactStorageImportStep, str] | None = Field(
        default=None,
        description="""
        Deprecated. Use storage_step_target_mappings instead.
        Mapping of import steps to storage names (string-based).
        These will be resolved via storage pool lookup.
        """,
        examples=[
            {"download": "fast-storage", "archive": "long-term-storage"},
        ],
    )
    storage_step_target_mappings: (
        Mapping[ArtifactStorageImportStep, ArtifactStorageTarget] | None
    ) = Field(
        default=None,
        description="""
        Mapping of import steps to structured storage targets.
        Each target can be either a NamedStorageTarget or a VFolderStorageTarget object.
        Takes precedence over storage_step_mappings for the same step.
        """,
        examples=[
            {
                "download": {"storage_name": "fast-storage"},
                "archive": {"storage_name": "long-term-storage"},
            },
            {
                "download": {"vfolder_id": "xxx", "volume_name": "volume1"},
                "archive": {"vfolder_id": "xxx", "volume_name": "volume1"},
            },
        ],
    )
    # Used by storage proxy to fetch verification results from remote reservoir.
    # Must have 1:1 correspondence with the models list.
    artifact_revision_ids: list[str] = Field(
        description="Artifact revision IDs corresponding to each model in the models list.",
    )
    storage_prefix: str | None = Field(
        default=None,
        description="""
        Custom prefix path for storing imported artifacts.
        - If not specified (None): Uses the artifact-type-specific default path.
          For models, the default is `{model_id}/{revision}`
          (e.g., "microsoft/DialoGPT-medium/main/").
          Default paths for other artifact types (PACKAGE, IMAGE) are not yet defined.
        - If set to "/": Files will be stored at the root without any prefix.
        - If set to a custom value (e.g., "my-models"): Files will be stored under
          the specified custom prefix.
        """,
        examples=["my-models", "custom/path", "/"],
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
    content_type: str | None = Field(
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


class VFSListFilesReq(BaseRequestModel):
    """
    Data model for listing files recursively in VFS storage.
    """

    directory: str = Field(
        description="The directory path within VFS storage to list files from.",
    )


class GetVerificationResultReq(BaseRequestModel):
    """Request for getting verification result of an artifact revision."""

    artifact_revision_id: uuid.UUID = Field(
        description="The artifact revision ID to get verification result."
    )


# Client-facing API token operation types
class TokenOperationType(StrEnum):
    DOWNLOAD = "download"
    UPLOAD = "upload"


# Client-facing API request models for download archive endpoint
class ArchiveDownloadTokenData(BaseModel):
    """Pydantic model for validating the JWT payload of archive download tokens."""

    operation: TokenOperationType
    volume: str
    vfolder_id: VFolderIDField
    files: list[str] = Field(min_length=1)
    exp: datetime
    model_config = ConfigDict(extra="allow")  # allow JWT-intrinsic keys


class ArchiveDownloadQueryParams(BaseRequestModel):
    """Pydantic model for archive download endpoint query parameters."""

    token: str = Field(description="JWT token containing download authorization")


class CreateArchiveDownloadSessionRequest(BaseRequestModel):
    """Request for creating an archive download session (JWT token generation)."""

    volume: str = Field(description="Volume name where the vfolder is located")
    vfid: VFolderIDField = Field(description="Virtual folder ID")
    files: list[str] = Field(
        min_length=1,
        description="List of relative file paths to include in the archive",
    )
