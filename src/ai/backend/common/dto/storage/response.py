import uuid
from typing import Optional

from pydantic import Field

from ai.backend.common.bgtask.types import TaskID
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


class HuggingFaceScanModelsResponse(BaseResponseModel):
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


class ReservoirImportModelsResponse(BaseResponseModel):
    """Response for Reservoir batch model import operation."""

    task_id: uuid.UUID = Field(
        description="""
        Unique identifier for the batch import task.
        Used to track the progress of the batch model import operation.
        """,
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
