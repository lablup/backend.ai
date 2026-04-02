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
    "AdminSearchArtifactRevisionsPayload",
    "AdminSearchArtifactsPayload",
    "ArtifactGQLNode",
    "ArtifactImportProgressUpdatedGQLPayload",
    "ArtifactNode",
    "ArtifactRevisionImportTaskInfo",
    "ArtifactRevisionImportTaskInfoGQL",
    "ArtifactRevisionNode",
    "ArtifactStatusChangedGQLPayload",
    "ArtifactVerificationGQLResultDTO",
    "ArtifactVerifierGQLResultDTO",
    "ArtifactVerifierGQLResultEntryDTO",
    "ArtifactVerifierMetadataEntryDTO",
    "ArtifactVerifierMetadataDTO",
    "ApproveArtifactGQLPayload",
    "ApproveRevisionPayload",
    "CancelImportArtifactGQLPayload",
    "CancelImportTaskPayload",
    "CleanupArtifactRevisionsGQLPayload",
    "CleanupRevisionsPayload",
    "DelegateImportArtifactsGQLPayload",
    "DelegateScanArtifactsGQLPayload",
    "DeleteArtifactsGQLPayload",
    "DeleteArtifactsPayload",
    "GetRevisionDownloadProgressPayload",
    "GetRevisionReadmePayload",
    "GetRevisionVerificationResultPayload",
    "ImportArtifactsGQLPayload",
    "ImportArtifactsPayload",
    "RejectArtifactGQLPayload",
    "RejectRevisionPayload",
    "RestoreArtifactsGQLPayload",
    "ScanArtifactsGQLPayload",
    "ScanArtifactModelsGQLPayload",
    "SourceInfoDTO",
    "UpdateArtifactGQLPayload",
    "UpdateArtifactPayload",
)


class ArtifactRevisionNode(BaseResponseModel):
    """Node model representing an artifact revision entity."""

    id: UUID = Field(description="Artifact revision ID")
    artifact_id: UUID = Field(description="Parent artifact ID")
    version: str = Field(description="Revision version string")
    size: str | None = Field(default=None, description="Revision size in bytes")
    status: ArtifactStatus = Field(description="Revision status")
    remote_status: str | None = Field(default=None, description="Remote status of the revision")
    created_at: datetime | None = Field(default=None, description="Creation timestamp")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp")
    digest: str | None = Field(default=None, description="Content digest of the revision")
    verification_result: VerificationStepResult | None = Field(
        default=None, description="Verification result from all verifiers"
    )
    readme: str | None = Field(default=None, description="README content of the revision")


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


class AdminSearchArtifactsPayload(BaseResponseModel):
    """Payload for admin artifact search result."""

    items: list[ArtifactNode] = Field(description="List of matching artifact nodes.")
    total_count: int = Field(description="Total number of matching artifacts.")
    has_next_page: bool
    has_previous_page: bool


class AdminSearchArtifactRevisionsPayload(BaseResponseModel):
    """Payload for admin artifact revision search result."""

    items: list[ArtifactRevisionNode] = Field(
        description="List of matching artifact revision nodes."
    )
    total_count: int = Field(description="Total number of matching artifact revisions.")
    has_next_page: bool
    has_previous_page: bool


class DeleteArtifactsPayload(BaseResponseModel):
    """Payload for artifact deletion result."""

    artifacts: list[ArtifactNode] = Field(description="List of deleted artifact nodes.")


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


# ---------------------------------------------------------------------------
# GQL-level DTOs (for Strawberry pydantic type integration)
# ---------------------------------------------------------------------------


class SourceInfoDTO(BaseResponseModel):
    """DTO for source/registry info used in GQL Artifact type."""

    name: str | None = Field(default=None, description="Name of the registry or source.")
    url: str | None = Field(default=None, description="URL of the registry or source.")


class ArtifactGQLNode(BaseResponseModel):
    """GQL-layer node DTO with resolved registry and source URLs."""

    id: UUID = Field(description="Artifact ID")
    name: str = Field(description="Artifact name")
    type: ArtifactType = Field(description="Artifact type")
    description: str | None = Field(default=None, description="Artifact description")
    registry: SourceInfoDTO = Field(description="Registry info with resolved URL")
    source: SourceInfoDTO = Field(description="Source registry info with resolved URL")
    readonly: bool = Field(description="Whether the artifact is readonly")
    extra: dict[str, Any] | None = Field(default=None, description="Extra metadata")
    scanned_at: datetime = Field(description="Last scanned timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    availability: ArtifactAvailability = Field(description="Artifact availability status")


class ArtifactVerifierMetadataEntryDTO(BaseResponseModel):
    """DTO for a single key-value verifier metadata entry."""

    key: str = Field(description="The key identifier for this metadata entry.")
    value: str = Field(description="The value for this metadata entry.")


class ArtifactVerifierMetadataDTO(BaseResponseModel):
    """DTO for verifier metadata containing multiple key-value entries."""

    entries: list[ArtifactVerifierMetadataEntryDTO] = Field(description="List of metadata entries.")


class ArtifactVerifierGQLResultDTO(BaseResponseModel):
    """DTO for a single verifier scan result."""

    success: bool = Field(description="Whether the verification completed successfully.")
    infected_count: int = Field(description="Number of infected or suspicious files detected.")
    scanned_at: datetime = Field(description="Timestamp when verification started.")
    scan_time: float = Field(description="Time taken to complete verification in seconds.")
    scanned_count: int = Field(description="Total number of files scanned.")
    metadata: ArtifactVerifierMetadataDTO = Field(
        description="Additional metadata from the verifier."
    )
    error: str | None = Field(
        default=None, description="Fatal error message if the verifier failed to complete."
    )


class ArtifactVerifierGQLResultEntryDTO(BaseResponseModel):
    """DTO for associating a verifier name with its scan result."""

    name: str = Field(description="Name of the verifier.")
    result: ArtifactVerifierGQLResultDTO = Field(description="Scan result from this verifier.")


class ArtifactVerificationGQLResultDTO(BaseResponseModel):
    """DTO for the complete verification result from all verifiers."""

    verifiers: list[ArtifactVerifierGQLResultEntryDTO] = Field(
        description="Results from each verifier that scanned the artifact."
    )


class ArtifactImportProgressUpdatedGQLPayload(BaseResponseModel):
    """GQL payload for artifact import progress subscription events."""

    artifact_id: UUID = Field(description="Artifact revision ID.")
    progress: float = Field(description="Import progress as a percentage.")
    status: str = Field(description="Current import status.")


class ArtifactRevisionImportTaskInfoGQL(BaseResponseModel):
    """GQL-level DTO for an artifact revision import task."""

    task_id: str | None = Field(default=None, description="Background task ID.")
    artifact_revision: ArtifactRevisionNode = Field(description="Artifact revision data.")


class ArtifactStatusChangedGQLPayload(BaseResponseModel):
    """GQL payload for artifact status change subscription events."""

    artifact_revision: ArtifactRevisionNode = Field(description="Updated artifact revision.")


class ScanArtifactsGQLPayload(BaseResponseModel):
    """GQL payload for artifact scanning operations."""

    artifacts: list[ArtifactNode] = Field(description="List of scanned artifacts.")


class DelegateScanArtifactsGQLPayload(BaseResponseModel):
    """GQL payload for delegated artifact scanning operations."""

    artifacts: list[ArtifactNode] = Field(
        description="List of artifacts discovered during the delegated scan."
    )


class ImportArtifactsGQLPayload(BaseResponseModel):
    """GQL payload for artifact import operations."""

    artifact_revisions: list[ArtifactRevisionNode] = Field(
        description="List of imported artifact revisions."
    )
    tasks: list[ArtifactRevisionImportTaskInfoGQL] = Field(
        description="List of import tasks created."
    )


class DelegateImportArtifactsGQLPayload(BaseResponseModel):
    """GQL payload for delegated artifact import operations."""

    artifact_revisions: list[ArtifactRevisionNode] = Field(
        description="List of imported artifact revisions from the reservoir registry's remote registry."
    )
    tasks: list[ArtifactRevisionImportTaskInfoGQL] = Field(
        description="List of background tasks created for importing the artifact revisions."
    )


class UpdateArtifactGQLPayload(BaseResponseModel):
    """GQL payload for artifact update operations."""

    artifact: ArtifactNode = Field(description="Updated artifact.")


class CleanupArtifactRevisionsGQLPayload(BaseResponseModel):
    """GQL payload for artifact revision cleanup operations."""

    artifact_revisions: list[ArtifactRevisionNode] = Field(
        description="Cleaned up artifact revisions."
    )


class ApproveArtifactGQLPayload(BaseResponseModel):
    """GQL payload for artifact revision approval operations."""

    artifact_revision: ArtifactRevisionNode = Field(description="Approved artifact revision.")


class RejectArtifactGQLPayload(BaseResponseModel):
    """GQL payload for artifact revision rejection operations."""

    artifact_revision: ArtifactRevisionNode = Field(description="Rejected artifact revision.")


class CancelImportArtifactGQLPayload(BaseResponseModel):
    """GQL payload for canceling artifact import operations."""

    artifact_revision: ArtifactRevisionNode = Field(
        description="Artifact revision with cancelled import."
    )


class ScanArtifactModelsGQLPayload(BaseResponseModel):
    """GQL payload for batch model scanning operations."""

    artifact_revision: list[ArtifactRevisionNode] = Field(
        description="Artifact revisions discovered during model scanning."
    )


class DeleteArtifactsGQLPayload(BaseResponseModel):
    """GQL payload for artifact deletion operations."""

    artifacts: list[ArtifactNode] = Field(description="List of soft-deleted artifacts.")


class RestoreArtifactsGQLPayload(BaseResponseModel):
    """GQL payload for artifact restoration operations."""

    artifacts: list[ArtifactNode] = Field(description="List of restored artifacts.")
