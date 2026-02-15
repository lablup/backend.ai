"""
Response DTOs for artifact registry system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.data.artifact.types import (
    ArtifactRegistryType,
    VerificationStepResult,
)

__all__ = (
    # DTOs
    "ArtifactRevisionDTO",
    "ArtifactDTO",
    "ArtifactWithRevisionsDTO",
    "ArtifactRevisionImportTaskDTO",
    "ArtifactRevisionReadmeDTO",
    # Responses
    "ScanArtifactsResponse",
    "DelegateScanArtifactsResponse",
    "DelegateImportArtifactsResponse",
    "SearchArtifactsResponse",
    "ScanArtifactModelsResponse",
    "RetrieveArtifactModelResponse",
)


# ---------------------------------------------------------------------------
# Data Transfer Objects
# ---------------------------------------------------------------------------


class ArtifactRevisionDTO(BaseModel):
    """Artifact revision data (without readme) for API responses."""

    id: UUID = Field(description="Revision ID")
    artifact_id: UUID = Field(description="Parent artifact ID")
    version: str = Field(description="Revision version string")
    size: int | None = Field(default=None, description="Total size in bytes")
    status: str = Field(description="Revision status")
    remote_status: str | None = Field(default=None, description="Remote status")
    created_at: datetime | None = Field(default=None, description="Creation timestamp")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp")
    digest: str | None = Field(default=None, description="Content digest")
    verification_result: VerificationStepResult | None = Field(
        default=None, description="Verification result"
    )


class ArtifactDTO(BaseModel):
    """Artifact data with revisions (without readme in revisions) for API responses."""

    id: UUID = Field(description="Artifact ID")
    name: str = Field(description="Artifact name")
    type: str = Field(description="Artifact type")
    description: str | None = Field(default=None, description="Artifact description")
    registry_id: UUID = Field(description="Registry ID")
    source_registry_id: UUID = Field(description="Source registry ID")
    registry_type: ArtifactRegistryType = Field(description="Registry type")
    source_registry_type: ArtifactRegistryType = Field(description="Source registry type")
    availability: str = Field(description="Artifact availability status")
    scanned_at: datetime = Field(description="When the artifact was scanned")
    updated_at: datetime = Field(description="When the artifact was last updated")
    readonly: bool = Field(description="Whether the artifact is read-only")
    extra: dict[str, Any] | None = Field(default=None, description="Extra metadata")
    revisions: list[ArtifactRevisionDTO] = Field(
        default_factory=list, description="Artifact revisions"
    )


class ArtifactRevisionDataDTO(BaseModel):
    """Full artifact revision data including readme."""

    id: UUID = Field(description="Revision ID")
    artifact_id: UUID = Field(description="Parent artifact ID")
    version: str = Field(description="Revision version string")
    readme: str | None = Field(default=None, description="Readme content")
    size: int | None = Field(default=None, description="Total size in bytes")
    status: str = Field(description="Revision status")
    remote_status: str | None = Field(default=None, description="Remote status")
    created_at: datetime | None = Field(default=None, description="Creation timestamp")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp")
    digest: str | None = Field(default=None, description="Content digest")
    verification_result: VerificationStepResult | None = Field(
        default=None, description="Verification result"
    )


class ArtifactWithRevisionsDTO(BaseModel):
    """Artifact data with full revisions (including readme) for single-model responses."""

    id: UUID = Field(description="Artifact ID")
    name: str = Field(description="Artifact name")
    type: str = Field(description="Artifact type")
    description: str | None = Field(default=None, description="Artifact description")
    registry_id: UUID = Field(description="Registry ID")
    source_registry_id: UUID = Field(description="Source registry ID")
    registry_type: ArtifactRegistryType = Field(description="Registry type")
    source_registry_type: ArtifactRegistryType = Field(description="Source registry type")
    availability: str = Field(description="Artifact availability status")
    scanned_at: datetime = Field(description="When the artifact was scanned")
    updated_at: datetime = Field(description="When the artifact was last updated")
    readonly: bool = Field(description="Whether the artifact is read-only")
    extra: dict[str, Any] | None = Field(default=None, description="Extra metadata")
    revisions: list[ArtifactRevisionDataDTO] = Field(
        default_factory=list, description="Artifact revisions with full data"
    )


class ArtifactRevisionImportTaskDTO(BaseModel):
    """Import task for an artifact revision."""

    task_id: str | None = Field(default=None, description="Background task ID")
    artifact_revision: ArtifactRevisionDTO = Field(description="The artifact revision")


class ArtifactRevisionReadmeDTO(BaseModel):
    """Readme data for an artifact revision."""

    readme: str | None = Field(default=None, description="Readme content")


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class ScanArtifactsResponse(BaseResponseModel):
    """Response for scanning external registries."""

    artifacts: list[ArtifactDTO] = Field(description="Scanned artifacts")


class DelegateScanArtifactsResponse(BaseResponseModel):
    """Response for scanning with delegation."""

    artifacts: list[ArtifactDTO] = Field(description="Scanned artifacts")
    source_registry_id: UUID = Field(description="Source registry ID")
    source_registry_type: ArtifactRegistryType = Field(description="Source registry type")
    readme_data: dict[str, ArtifactRevisionReadmeDTO] = Field(
        default_factory=dict, description="Readme data keyed by revision ID"
    )


class DelegateImportArtifactsResponse(BaseResponseModel):
    """Response for importing artifacts with delegation."""

    tasks: list[ArtifactRevisionImportTaskDTO] = Field(description="Import tasks")


class SearchArtifactsResponse(BaseResponseModel):
    """Response for searching registered artifacts."""

    artifacts: list[ArtifactDTO] = Field(description="Matched artifacts")


class ScanArtifactModelsResponse(BaseResponseModel):
    """Response for batch scanning models."""

    artifacts: list[ArtifactDTO] = Field(description="Scanned model artifacts")


class RetrieveArtifactModelResponse(BaseResponseModel):
    """Response for scanning a single model."""

    artifact: ArtifactWithRevisionsDTO = Field(description="Model artifact with full revision data")
