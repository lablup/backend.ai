"""
Response DTOs for artifact DTO v2.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

from .types import (
    ArtifactAvailability,
    ArtifactRegistryType,
    ArtifactStatus,
    ArtifactType,
    CombinedDownloadProgress,
    VerificationStepResult,
)

__all__ = (
    "ArtifactNode",
    "ArtifactRevisionImportTaskInfo",
    "ArtifactRevisionNode",
    "ApproveRevisionPayload",
    "CancelImportTaskPayload",
    "CleanupRevisionsPayload",
    "GetRevisionDownloadProgressPayload",
    "GetRevisionReadmePayload",
    "GetRevisionVerificationResultPayload",
    "ImportArtifactsPayload",
    "RejectRevisionPayload",
    "UpdateArtifactPayload",
)


class ArtifactRevisionNode(BaseResponseModel):
    """Node model representing an artifact revision entity."""

    id: UUID = Field(description="Artifact revision ID")
    artifact_id: UUID = Field(description="Parent artifact ID")
    version: str = Field(description="Revision version string")
    size: int | None = Field(default=None, description="Revision size in bytes")
    status: ArtifactStatus = Field(description="Revision status")
    remote_status: str | None = Field(default=None, description="Remote status of the revision")
    created_at: datetime | None = Field(default=None, description="Creation timestamp")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp")
    digest: str | None = Field(default=None, description="Content digest of the revision")
    verification_result: VerificationStepResult | None = Field(
        default=None, description="Verification result from all verifiers"
    )


class ArtifactNode(BaseResponseModel):
    """Node model representing an artifact entity with optional nested revisions."""

    id: UUID = Field(description="Artifact ID")
    name: str = Field(description="Artifact name")
    type: ArtifactType = Field(description="Artifact type")
    description: str | None = Field(default=None, description="Artifact description")
    registry_id: UUID = Field(description="Registry ID where artifact is stored")
    source_registry_id: UUID = Field(description="Source registry ID of the artifact")
    registry_type: ArtifactRegistryType = Field(description="Registry type")
    source_registry_type: ArtifactRegistryType = Field(description="Source registry type")
    availability: ArtifactAvailability = Field(description="Artifact availability status")
    scanned_at: datetime = Field(description="Last scanned timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    readonly: bool = Field(description="Whether the artifact is readonly")
    extra: dict[str, Any] | None = Field(default=None, description="Extra metadata")
    revisions: list[ArtifactRevisionNode] = Field(
        default_factory=list, description="List of artifact revisions"
    )


class ArtifactRevisionImportTaskInfo(BaseResponseModel):
    """Info model for an artifact revision import task."""

    task_id: str | None = Field(default=None, description="Background task ID")
    artifact_revision: ArtifactRevisionNode = Field(description="Artifact revision data")


class UpdateArtifactPayload(BaseResponseModel):
    """Payload for artifact update mutation result."""

    artifact: ArtifactNode = Field(description="Updated artifact")


class ImportArtifactsPayload(BaseResponseModel):
    """Payload for artifact import mutation result."""

    tasks: list[ArtifactRevisionImportTaskInfo] = Field(description="List of import tasks")


class CleanupRevisionsPayload(BaseResponseModel):
    """Payload for artifact revision cleanup mutation result."""

    artifact_revisions: list[ArtifactRevisionNode] = Field(
        description="Cleaned up artifact revisions"
    )


class ApproveRevisionPayload(BaseResponseModel):
    """Payload for artifact revision approval mutation result."""

    artifact_revision: ArtifactRevisionNode = Field(description="Approved artifact revision")


class RejectRevisionPayload(BaseResponseModel):
    """Payload for artifact revision rejection mutation result."""

    artifact_revision: ArtifactRevisionNode = Field(description="Rejected artifact revision")


class CancelImportTaskPayload(BaseResponseModel):
    """Payload for import task cancellation mutation result."""

    artifact_revision: ArtifactRevisionNode = Field(
        description="Artifact revision with cancelled import"
    )


class GetRevisionReadmePayload(BaseResponseModel):
    """Payload for artifact revision README retrieval."""

    readme: str | None = Field(default=None, description="README content of the revision")


class GetRevisionVerificationResultPayload(BaseResponseModel):
    """Payload for artifact revision verification result retrieval."""

    verification_result: VerificationStepResult | None = Field(
        default=None, description="Verification result from all verifiers"
    )


class GetRevisionDownloadProgressPayload(BaseResponseModel):
    """Payload for artifact revision download progress retrieval."""

    download_progress: CombinedDownloadProgress = Field(
        description="Combined local and remote download progress"
    )
