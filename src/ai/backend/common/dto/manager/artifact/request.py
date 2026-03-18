"""
Request DTOs for artifact system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = (
    "ImportArtifactsOptions",
    "ImportArtifactsRequest",
    "UpdateArtifactRequest",
    "CleanupRevisionsRequest",
    "CancelImportTaskRequest",
)


class ImportArtifactsOptions(BaseRequestModel):
    """Options for importing artifact revisions."""

    force: bool = Field(
        default=False,
        description="Force re-download regardless of digest freshness check.",
    )


class ImportArtifactsRequest(BaseRequestModel):
    """Request to import scanned artifact revisions from external registries."""

    artifact_revision_ids: list[UUID] = Field(
        description="List of artifact revision IDs to import.",
    )
    vfolder_id: UUID | None = Field(
        default=None,
        description="Optional vfolder ID to import artifacts directly into.",
    )
    options: ImportArtifactsOptions | None = Field(
        default=None,
        description="Options controlling import behavior such as forcing re-download.",
    )


class UpdateArtifactRequest(BaseRequestModel):
    """Request to update artifact metadata."""

    readonly: bool | None = Field(
        default=None,
        description="Whether the artifact should be readonly.",
    )
    description: str | None = Field(
        default=None,
        description="Updated description.",
    )


class CleanupRevisionsRequest(BaseRequestModel):
    """Request to clean up artifact revision data."""

    artifact_revision_ids: list[UUID] = Field(
        description="List of artifact revision IDs to cleanup.",
    )


class CancelImportTaskRequest(BaseRequestModel):
    """Request to cancel an in-progress artifact import task."""

    artifact_revision_id: UUID = Field(
        description="The artifact revision ID to cancel import.",
    )
