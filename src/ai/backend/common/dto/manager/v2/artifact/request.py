"""
Request DTOs for artifact DTO v2.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field, field_validator

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel
from ai.backend.common.dto.manager.query import StringFilter

from .types import (
    ArtifactAvailabilityFilter,
    ArtifactOrderField,
    ArtifactTypeFilter,
    OrderDirection,
)

__all__ = (
    "AdminSearchArtifactsInput",
    "ArtifactFilter",
    "ArtifactOrder",
    "CancelImportTaskInput",
    "CleanupRevisionsInput",
    "DeleteArtifactsInput",
    "ImportArtifactsInput",
    "UpdateArtifactInput",
)


class UpdateArtifactInput(BaseRequestModel):
    """Input for updating artifact metadata."""

    readonly: bool | None = Field(
        default=None,
        description="Whether the artifact should be readonly. None means no change.",
    )
    description: str | Sentinel | None = Field(
        default=SENTINEL,
        description="Updated description. Use SENTINEL to clear the field; None means no change.",
    )

    @field_validator("description", mode="before")
    @classmethod
    def description_strip_whitespace(cls, v: str | Sentinel | None) -> str | Sentinel | None:
        if isinstance(v, str):
            stripped = v.strip()
            return stripped if stripped else None
        return v


class ImportArtifactsInput(BaseRequestModel):
    """Input for importing scanned artifact revisions from external registries."""

    artifact_revision_ids: list[UUID] = Field(
        description="List of artifact revision IDs to import.",
    )
    vfolder_id: UUID | None = Field(
        default=None,
        description="Optional vfolder ID to import artifacts directly into.",
    )
    force: bool = Field(
        default=False,
        description="Force re-download regardless of digest freshness check.",
    )


class CleanupRevisionsInput(BaseRequestModel):
    """Input for cleaning up artifact revision data."""

    artifact_revision_ids: list[UUID] = Field(
        description="List of artifact revision IDs to cleanup.",
    )


class ArtifactFilter(BaseRequestModel):
    """Filter conditions for artifact search."""

    name: StringFilter | None = Field(default=None, description="Filter by artifact name.")
    type: ArtifactTypeFilter | None = Field(default=None, description="Filter by artifact type.")
    availability: ArtifactAvailabilityFilter | None = Field(
        default=None, description="Filter by artifact availability."
    )


class ArtifactOrder(BaseRequestModel):
    """Order specification for artifact search."""

    field: ArtifactOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction.")


class AdminSearchArtifactsInput(BaseRequestModel):
    """Input for searching artifacts with filters, orders, and pagination.

    Supports two pagination modes (mutually exclusive):
    - Cursor-based: first/after (forward) or last/before (backward)
    - Offset-based: limit/offset
    """

    filter: ArtifactFilter | None = Field(default=None, description="Filter conditions.")
    order: list[ArtifactOrder] | None = Field(default=None, description="Order specifications.")
    # Cursor-based pagination (Relay)
    first: int | None = Field(default=None, ge=1, description="Number of items from the start.")
    after: str | None = Field(default=None, description="Cursor to paginate forward from.")
    last: int | None = Field(default=None, ge=1, description="Number of items from the end.")
    before: str | None = Field(default=None, description="Cursor to paginate backward from.")
    # Offset-based pagination
    limit: int | None = Field(default=None, ge=1, description="Maximum number of items to return.")
    offset: int | None = Field(default=None, ge=0, description="Number of items to skip.")


class DeleteArtifactsInput(BaseRequestModel):
    """Input for deleting multiple artifacts by ID."""

    artifact_ids: list[UUID] = Field(description="List of artifact IDs to delete.")


class CancelImportTaskInput(BaseRequestModel):
    """Input for cancelling an in-progress artifact import task."""

    artifact_revision_id: UUID = Field(
        description="The artifact revision ID whose import task should be cancelled.",
    )
