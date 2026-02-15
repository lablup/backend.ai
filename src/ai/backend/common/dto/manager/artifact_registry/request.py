"""
Request DTOs for artifact registry system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.data.storage.registries.types import ModelTarget
from ai.backend.common.dto.manager.query import StringFilter

__all__ = (
    # Nested types
    "DelegateeTargetInput",
    "ImportArtifactsOptionsInput",
    "PaginationInput",
    "ForwardPaginationInput",
    "BackwardPaginationInput",
    "OffsetPaginationInput",
    "ArtifactOrderingInput",
    "ArtifactFilterInput",
    # Requests
    "ScanArtifactsRequest",
    "DelegateScanArtifactsRequest",
    "DelegateImportArtifactsRequest",
    "SearchArtifactsRequest",
    "ScanArtifactModelsRequest",
)


# ---------------------------------------------------------------------------
# Nested input types
# ---------------------------------------------------------------------------


class DelegateeTargetInput(BaseModel):
    """Target reservoir for delegation operations."""

    delegatee_reservoir_id: UUID = Field(description="ID of the delegatee reservoir")
    target_registry_id: UUID = Field(description="ID of the target registry")


class ImportArtifactsOptionsInput(BaseRequestModel):
    """Options for importing artifact revisions."""

    force: bool = Field(
        default=False,
        description="Force re-download regardless of digest freshness check.",
    )


class ForwardPaginationInput(BaseRequestModel):
    """Forward pagination: fetch items after a given cursor."""

    after: str | None = Field(default=None, description="Cursor to start after")
    first: int | None = Field(default=None, description="Number of items to fetch")


class BackwardPaginationInput(BaseRequestModel):
    """Backward pagination: fetch items before a given cursor."""

    before: str | None = Field(default=None, description="Cursor to start before")
    last: int | None = Field(default=None, description="Number of items to fetch")


class OffsetPaginationInput(BaseRequestModel):
    """Standard offset/limit pagination options."""

    offset: int | None = Field(default=None, description="Number of items to skip")
    limit: int | None = Field(default=None, description="Maximum items to return")


class PaginationInput(BaseRequestModel):
    """Pagination options supporting cursor-based and offset-based pagination."""

    forward: ForwardPaginationInput | None = Field(
        default=None, description="Forward cursor-based pagination"
    )
    backward: BackwardPaginationInput | None = Field(
        default=None, description="Backward cursor-based pagination"
    )
    offset: OffsetPaginationInput | None = Field(
        default=None, description="Offset-based pagination"
    )


class ArtifactOrderingInput(BaseRequestModel):
    """Ordering options for artifact queries."""

    order_by: list[tuple[str, bool]] = Field(
        default_factory=lambda: [("NAME", False)],
        description="List of (field, descending) tuples",
    )


class ArtifactFilterInput(BaseRequestModel):
    """Filtering options for artifacts."""

    artifact_type: list[str] | None = Field(default=None, description="Filter by artifact type(s)")
    name_filter: StringFilter | None = Field(default=None, description="Filter by name")
    registry_filter: StringFilter | None = Field(
        default=None, description="Filter by registry name"
    )
    source_filter: StringFilter | None = Field(default=None, description="Filter by source name")
    registry_id: UUID | None = Field(default=None, description="Filter by registry ID")
    registry_type: ArtifactRegistryType | None = Field(
        default=None, description="Filter by registry type"
    )
    source_registry_id: UUID | None = Field(
        default=None, description="Filter by source registry ID"
    )
    source_registry_type: ArtifactRegistryType | None = Field(
        default=None, description="Filter by source registry type"
    )
    availability: list[str] | None = Field(
        default=None, description="Filter by availability status"
    )
    AND: list[ArtifactFilterInput] | None = Field(default=None, description="AND filter group")
    OR: list[ArtifactFilterInput] | None = Field(default=None, description="OR filter group")
    NOT: list[ArtifactFilterInput] | None = Field(default=None, description="NOT filter group")


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class ScanArtifactsRequest(BaseRequestModel):
    """Request body for scanning external registries."""

    registry_id: UUID | None = Field(
        default=None, description="The unique identifier of the artifact registry to scan."
    )
    artifact_type: str | None = Field(default=None, description="Artifact type filter")
    limit: int = Field(description="Maximum number of artifacts to scan")
    order: str | None = Field(default=None, description="Sort order key")
    search: str | None = Field(default=None, description="Search query string")


class DelegateScanArtifactsRequest(BaseRequestModel):
    """Request body for scanning with delegation."""

    delegator_reservoir_id: UUID | None = Field(
        default=None,
        description="ID of the reservoir registry to delegate the scan request to",
    )
    delegatee_target: DelegateeTargetInput | None = Field(
        default=None,
        description="The target reservoir to delegate the scan.",
    )
    artifact_type: str | None = Field(default=None, description="Artifact type filter")
    limit: int = Field(description="Maximum number of artifacts to scan")
    order: str | None = Field(default=None, description="Sort order key")
    search: str | None = Field(default=None, description="Search query string")


class DelegateImportArtifactsRequest(BaseRequestModel):
    """Request body for importing artifacts with delegation."""

    artifact_revision_ids: list[UUID] = Field(
        description="List of artifact revision IDs to delegate the import request."
    )
    delegator_reservoir_id: UUID | None = Field(
        default=None,
        description="ID of the reservoir registry to delegate the import request to",
    )
    delegatee_target: DelegateeTargetInput | None = Field(
        default=None, description="The target reservoir to delegate the import."
    )
    artifact_type: str | None = Field(default=None, description="Artifact type filter")
    options: ImportArtifactsOptionsInput = Field(
        default_factory=ImportArtifactsOptionsInput,
        description="Options controlling import behavior such as forcing re-download.",
    )


class SearchArtifactsRequest(BaseRequestModel):
    """Request body for searching registered artifacts."""

    pagination: PaginationInput = Field(description="Pagination options")
    ordering: ArtifactOrderingInput | None = Field(default=None, description="Ordering options")
    filters: ArtifactFilterInput | None = Field(default=None, description="Filter options")


class ScanArtifactModelsRequest(BaseRequestModel):
    """Request body for batch scanning models."""

    models: list[ModelTarget] = Field(description="List of models to scan from the registry.")
    registry_id: UUID | None = Field(
        default=None, description="The unique identifier of the artifact registry to scan."
    )
