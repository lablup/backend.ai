"""
Response DTOs for artifact system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.data.artifact.types import (
    CombinedDownloadProgress,
    VerificationStepResult,
)

__all__ = (
    # DTOs
    "ArtifactRevisionDTO",
    "ArtifactDTO",
    "ArtifactRevisionImportTaskDTO",
    # Responses
    "ImportArtifactsResponse",
    "UpdateArtifactResponse",
    "CleanupRevisionsResponse",
    "ApproveRevisionResponse",
    "RejectRevisionResponse",
    "CancelImportTaskResponse",
    "GetRevisionReadmeResponse",
    "GetRevisionVerificationResultResponse",
    "GetRevisionDownloadProgressResponse",
)


class ArtifactRevisionDTO(BaseModel):
    """DTO for artifact revision data."""

    id: UUID = Field(description="Artifact revision ID")
    artifact_id: UUID = Field(description="Parent artifact ID")
    version: str = Field(description="Revision version string")
    size: int | None = Field(default=None, description="Revision size in bytes")
    status: str = Field(description="Revision status")
    remote_status: str | None = Field(default=None, description="Remote status")
    created_at: datetime | None = Field(default=None, description="Creation timestamp")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp")
    digest: str | None = Field(default=None, description="Content digest")
    verification_result: VerificationStepResult | None = Field(
        default=None, description="Verification result"
    )


class ArtifactDTO(BaseModel):
    """DTO for artifact data."""

    id: UUID = Field(description="Artifact ID")
    name: str = Field(description="Artifact name")
    type: str = Field(description="Artifact type")
    description: str | None = Field(default=None, description="Artifact description")
    registry_id: UUID = Field(description="Registry ID")
    source_registry_id: UUID = Field(description="Source registry ID")
    registry_type: str = Field(description="Registry type")
    source_registry_type: str = Field(description="Source registry type")
    availability: str = Field(description="Artifact availability")
    scanned_at: datetime = Field(description="Last scanned timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    readonly: bool = Field(description="Whether the artifact is readonly")
    extra: dict[str, Any] | None = Field(default=None, description="Extra metadata")


class ArtifactRevisionImportTaskDTO(BaseModel):
    """DTO for an artifact revision import task."""

    task_id: str | None = Field(default=None, description="Background task ID")
    artifact_revision: ArtifactRevisionDTO = Field(description="Artifact revision data")


class ImportArtifactsResponse(BaseResponseModel):
    """Response for importing artifact revisions."""

    tasks: list[ArtifactRevisionImportTaskDTO] = Field(description="List of import tasks")


class UpdateArtifactResponse(BaseResponseModel):
    """Response for updating artifact metadata."""

    artifact: ArtifactDTO = Field(description="Updated artifact data")


class CleanupRevisionsResponse(BaseResponseModel):
    """Response for cleaning up artifact revisions."""

    artifact_revisions: list[ArtifactRevisionDTO] = Field(
        description="Cleaned up artifact revisions"
    )


class ApproveRevisionResponse(BaseResponseModel):
    """Response for approving an artifact revision."""

    artifact_revision: ArtifactRevisionDTO = Field(description="Approved artifact revision")


class RejectRevisionResponse(BaseResponseModel):
    """Response for rejecting an artifact revision."""

    artifact_revision: ArtifactRevisionDTO = Field(description="Rejected artifact revision")


class CancelImportTaskResponse(BaseResponseModel):
    """Response for cancelling an import task."""

    artifact_revision: ArtifactRevisionDTO = Field(
        description="Artifact revision with cancelled import"
    )


class GetRevisionReadmeResponse(BaseResponseModel):
    """Response for getting artifact revision README."""

    readme: str | None = Field(default=None, description="README content")


class GetRevisionVerificationResultResponse(BaseResponseModel):
    """Response for getting artifact revision verification result."""

    verification_result: VerificationStepResult | None = Field(
        default=None, description="Verification result"
    )


class GetRevisionDownloadProgressResponse(BaseResponseModel):
    """Response for getting artifact revision download progress."""

    download_progress: CombinedDownloadProgress = Field(description="Download progress data")
