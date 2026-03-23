"""
Response DTOs for artifact registry DTO v2.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.artifact.response import (
    ArtifactNode,
    ArtifactRevisionImportTaskInfo,
    ArtifactRevisionNode,
)
from ai.backend.common.dto.manager.v2.artifact.types import VerificationStepResult

from .types import (
    ArtifactRegistryType,
    ArtifactRevisionReadmeInfo,
)

__all__ = (
    # Node models defined in this module
    "ArtifactRegistryGQLNode",
    "ArtifactRevisionDataNode",
    "ArtifactWithRevisionsNode",
    # Re-exported from v2/artifact for convenience
    "ArtifactNode",
    "ArtifactRevisionImportTaskInfo",
    "ArtifactRevisionNode",
    # Payload models
    "DelegateImportArtifactsPayload",
    "DelegateScanArtifactsPayload",
    "RetrieveArtifactModelPayload",
    "ScanArtifactModelsPayload",
    "ScanArtifactsPayload",
    "SearchArtifactsPayload",
)


# ---------------------------------------------------------------------------
# Node models
# ---------------------------------------------------------------------------


class ArtifactRegistryGQLNode(BaseResponseModel):
    """DTO for ArtifactRegistry GQL type."""

    id: UUID = Field(description="Internal identifier of the artifact registry metadata record.")
    registry_id: UUID = Field(description="Identifier of the actual registry implementation.")
    name: str = Field(description="Name of the artifact registry.")
    type: ArtifactRegistryType = Field(description="Type of the artifact registry.")


class ArtifactRevisionDataNode(BaseResponseModel):
    """Full revision data including readme, for single-model or delegated scan responses."""

    id: UUID = Field(description="Artifact revision ID")
    artifact_id: UUID = Field(description="Parent artifact ID")
    version: str = Field(description="Revision version string")
    readme: str | None = Field(default=None, description="README content for this revision")
    size: int | None = Field(default=None, description="Revision size in bytes")
    status: str = Field(description="Revision status")
    remote_status: str | None = Field(default=None, description="Remote status of the revision")
    created_at: datetime | None = Field(default=None, description="Creation timestamp")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp")
    digest: str | None = Field(default=None, description="Content digest of the revision")
    verification_result: VerificationStepResult | None = Field(
        default=None, description="Verification result from all verifiers"
    )


class ArtifactWithRevisionsNode(BaseResponseModel):
    """Artifact node with full revision data (including readme) for single-model retrieval."""

    id: UUID = Field(description="Artifact ID")
    name: str = Field(description="Artifact name")
    type: str = Field(description="Artifact type")
    description: str | None = Field(default=None, description="Artifact description")
    registry_id: UUID = Field(description="Registry ID where artifact is stored")
    source_registry_id: UUID = Field(description="Source registry ID of the artifact")
    registry_type: ArtifactRegistryType = Field(description="Registry type")
    source_registry_type: ArtifactRegistryType = Field(description="Source registry type")
    availability: str = Field(description="Artifact availability status")
    scanned_at: datetime = Field(description="Last scanned timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    readonly: bool = Field(description="Whether the artifact is readonly")
    extra: dict[str, Any] | None = Field(default=None, description="Extra metadata")
    revisions: list[ArtifactRevisionDataNode] = Field(
        default_factory=list,
        description="List of artifact revisions with full data including readme",
    )


# ---------------------------------------------------------------------------
# Payload models
# ---------------------------------------------------------------------------


class ScanArtifactsPayload(BaseResponseModel):
    """Payload for scanning external registries."""

    artifacts: list[ArtifactNode] = Field(description="Scanned artifacts")


class DelegateScanArtifactsPayload(BaseResponseModel):
    """Payload for scanning with delegation, including readme data."""

    artifacts: list[ArtifactNode] = Field(description="Scanned artifacts")
    source_registry_id: UUID = Field(description="Source registry ID used for the delegated scan")
    source_registry_type: ArtifactRegistryType = Field(
        description="Source registry type used for the delegated scan"
    )
    readme_data: dict[str, ArtifactRevisionReadmeInfo] = Field(
        default_factory=dict,
        description="README data keyed by artifact revision ID string",
    )


class DelegateImportArtifactsPayload(BaseResponseModel):
    """Payload for importing artifacts with delegation."""

    tasks: list[ArtifactRevisionImportTaskInfo] = Field(
        description="List of import tasks for the delegated artifact revisions"
    )


class SearchArtifactsPayload(BaseResponseModel):
    """Payload for searching registered artifacts."""

    artifacts: list[ArtifactNode] = Field(description="Matched artifacts")


class ScanArtifactModelsPayload(BaseResponseModel):
    """Payload for batch scanning models."""

    artifacts: list[ArtifactNode] = Field(description="Scanned model artifacts")


class RetrieveArtifactModelPayload(BaseResponseModel):
    """Payload for retrieving a single model artifact with full revision data."""

    artifact: ArtifactWithRevisionsNode = Field(
        description="Model artifact with full revision data including readme"
    )
