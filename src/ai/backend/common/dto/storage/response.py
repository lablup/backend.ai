import uuid
from typing import Optional

from pydantic import Field

from ai.backend.common.bgtask.types import TaskID
from ai.backend.common.data.artifact.types import VerificationStepResult
from ai.backend.common.data.storage.registries.types import ModelData

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


class PresignedUploadObjectResponse(BaseResponseModel):
    url: str
    fields: dict[str, str]


class PresignedDownloadObjectResponse(BaseResponseModel):
    url: str


class ObjectMetaResponse(BaseResponseModel):
    content_length: Optional[int]
    content_type: Optional[str]
    last_modified: Optional[str]
    etag: Optional[str]
    metadata: dict[str, str]


class VFolderCloneResponse(BaseResponseModel):
    bgtask_id: TaskID


class VFolderDeleteResponse(BaseResponseModel):
    bgtask_id: TaskID


class FileDeleteAsyncResponse(BaseResponseModel):
    """Response for asynchronous file deletion operation."""

    bgtask_id: TaskID = Field(
        description="""
        Unique identifier for the background file deletion task.
        Use this ID to subscribe to task progress updates via GraphQL subscriptions
        or to check the current status of the deletion operation.
        The task transitions through states: ONGOING → SUCCESS/FAILURE/CANCELLED.
        """,
    )


class HuggingFaceScanModelsResponse(BaseResponseModel):
    """Response for HuggingFace scan operation."""

    models: list[ModelData] = Field(
        default_factory=list,
        description="""
        List of HuggingFace models scanned and retrieved.
        Each model includes comprehensive metadata and file information.
        """,
    )


class HuggingFaceScanModelsSyncResponse(BaseResponseModel):
    """Response for HuggingFace scan operation."""

    models: list[ModelData] = Field(
        default_factory=list,
        description="""
        List of HuggingFace models scanned and retrieved.
        Each model includes comprehensive metadata and file information.
        """,
    )


class HuggingFaceRetrieveModelsResponse(BaseResponseModel):
    """Response for HuggingFace retrieve operation."""

    models: list[ModelData] = Field(
        default_factory=list,
        description="""
        List of HuggingFace models scanned and retrieved.
        Each model includes comprehensive metadata and file information.
        """,
    )


class HuggingFaceRetrieveModelResponse(BaseResponseModel):
    """Response for HuggingFace retrieve operation."""

    model: ModelData = Field(
        description="""
        HuggingFace model scanned and retrieved.
        The model includes comprehensive metadata and file information.
        """,
    )


class HuggingFaceImportModelsResponse(BaseResponseModel):
    """Response for HuggingFace batch model import operation."""

    task_id: uuid.UUID = Field(
        description="""
        Unique identifier for the batch import task.
        Used to track the progress of the batch model import operation.
        """,
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )


class HuggingFaceGetCommitHashResponse(BaseResponseModel):
    """Response for getting HuggingFace model commit hash."""

    commit_hash: Optional[str] = Field(
        description="""
        The commit hash (SHA) for the specific model revision.
        Returns null if commit hash is not available.
        """,
        examples=["607a30d783dfa663caf39e06633721c8d4cfcd7e", None],
    )


class ReservoirImportModelsResponse(BaseResponseModel):
    """Response for Reservoir batch model import operation."""

    task_id: uuid.UUID = Field(
        description="""
        Unique identifier for the batch import task.
        Used to track the progress of the batch model import operation.
        """,
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )


# VFS Storage Response DTOs
class VFSFileMetaResponse(BaseResponseModel):
    """Response for VFS file metadata operations."""

    filepath: str = Field(description="The file path within VFS storage.")
    content_length: Optional[int] = Field(description="Size of the file in bytes.")
    content_type: Optional[str] = Field(description="MIME type of the file.")
    last_modified: Optional[float] = Field(description="Last modification time as Unix timestamp.")
    created: Optional[float] = Field(description="Creation time as Unix timestamp.")
    is_directory: bool = Field(description="Whether this is a directory.")
    metadata: dict[str, str] = Field(default_factory=dict, description="Additional file metadata.")


class VFSOperationResponse(BaseResponseModel):
    """Generic response for VFS operations that don't return specific data."""

    filepath: Optional[str] = Field(
        default=None, description="The file/directory path that was operated on."
    )


class VFSUploadResponse(BaseResponseModel):
    """Response for VFS file upload operations."""

    filepath: str = Field(description="The path of the uploaded file.")


class VFSDeleteResponse(BaseResponseModel):
    """Response for VFS file/directory delete operations."""

    filepath: str = Field(description="The path of the deleted file or directory.")


class VFSFileInfo(BaseResponseModel):
    """Information about a single file or directory in VFS storage."""

    name: str = Field(description="Name of the file or directory.")
    type: str = Field(description="Type of the entry: 'file' or 'directory'.")
    size: Optional[int] = Field(
        default=None, description="Size of the file in bytes (None for directories)."
    )
    modified: float = Field(description="Last modification time as Unix timestamp.")
    created: float = Field(description="Creation time as Unix timestamp.")
    path: str = Field(description="Relative path from the base directory.")


class VFSListFilesResponse(BaseResponseModel):
    """Response for VFS recursive file listing operations."""

    files: list[VFSFileInfo] = Field(
        default_factory=list, description="List of all files and directories found recursively."
    )


class GetVerificationResultResponse(BaseResponseModel):
    """Response for getting verification result of an artifact revision."""

    verification_result: Optional[VerificationStepResult] = Field(
        default=None,
        description="The verification result for the artifact revision.",
    )
