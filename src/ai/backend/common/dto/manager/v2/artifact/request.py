"""
Request DTOs for artifact DTO v2.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field, field_validator

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel
from ai.backend.common.dto.manager.query import IntFilter, StringFilter, UUIDFilter

from .types import (
    ArtifactAvailability,
    ArtifactAvailabilityFilter,
    ArtifactOrderField,
    ArtifactRemoteStatus,
    ArtifactRevisionOrderField,
    ArtifactStatus,
    ArtifactType,
    ArtifactTypeFilter,
    OrderDirection,
)

__all__ = (
    "AdminSearchArtifactRevisionsInput",
    "AdminSearchArtifactsGQLInput",
    "AdminSearchArtifactsInput",
    "ApproveArtifactInput",
    "ArtifactFilter",
    "ArtifactGQLFilterInputDTO",
    "ArtifactGQLOrderByInputDTO",
    "ArtifactOrder",
    "ArtifactRevisionGQLFilterInputDTO",
    "ArtifactRevisionGQLOrderByInputDTO",
    "ArtifactRevisionRemoteStatusFilterDTO",
    "ArtifactRevisionStatusFilterDTO",
    "ArtifactStatusChangedInputDTO",
    "CancelImportTaskInput",
    "CleanupRevisionsInput",
    "DeleteArtifactsInput",
    "DelegateeTargetInput",
    "DelegateImportArtifactsInput",
    "DelegateScanArtifactsInput",
    "ImportArtifactsInput",
    "ImportArtifactsOptionsInput",
    "ModelTargetInput",
    "RejectArtifactInput",
    "RestoreArtifactsInput",
    "ScanArtifactModelsInput",
    "ScanArtifactsInput",
    "UpdateArtifactGQLInput",
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


class ImportArtifactsOptionsInput(BaseRequestModel):
    """Options for importing artifact revisions."""

    force: bool = Field(
        default=False,
        description="Force re-download regardless of digest freshness check.",
    )


class ImportArtifactsInput(BaseRequestModel):
    """Input for importing scanned artifact revisions from external registries."""

    artifact_revision_ids: list[UUID] = Field(
        description="List of artifact revision IDs to import.",
    )
    vfolder_id: UUID | None = Field(
        default=None,
        description="Optional vfolder ID to import artifacts directly into.",
    )
    options: ImportArtifactsOptionsInput | None = Field(
        default=None,
        description="Options controlling import behavior such as forcing re-download.",
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


class RestoreArtifactsInput(BaseRequestModel):
    """Input for restoring previously deleted artifacts."""

    artifact_ids: list[UUID] = Field(description="List of artifact IDs to restore.")


class ApproveArtifactInput(BaseRequestModel):
    """Input for approving an artifact revision."""

    artifact_revision_id: UUID = Field(
        description="The artifact revision ID to approve.",
    )


class RejectArtifactInput(BaseRequestModel):
    """Input for rejecting an artifact revision."""

    artifact_revision_id: UUID = Field(
        description="The artifact revision ID to reject.",
    )


class ScanArtifactsInput(BaseRequestModel):
    """Input for scanning artifacts from external registries."""

    registry_id: UUID | None = Field(
        default=None,
        description="Optional registry ID to scan artifacts from.",
    )
    limit: int = Field(
        description="Maximum number of artifacts to scan.",
    )
    artifact_type: ArtifactType | None = Field(
        default=None,
        description="Filter artifacts by type.",
    )
    search: str | None = Field(
        default=None,
        description="Search term to filter artifacts by name or description.",
    )


class DelegateeTargetInput(BaseRequestModel):
    """Target delegatee for delegated scan/import operations."""

    delegatee_reservoir_id: UUID = Field(
        description="ID of the delegatee reservoir registry.",
    )
    target_registry_id: UUID = Field(
        description="ID of the target registry within the delegatee reservoir.",
    )


class DelegateScanArtifactsInput(BaseRequestModel):
    """Input for delegated scanning of artifacts from a reservoir registry."""

    delegator_reservoir_id: UUID | None = Field(
        default=None,
        description="ID of the reservoir registry to delegate the scan request to.",
    )
    delegatee_target: DelegateeTargetInput | None = Field(
        default=None,
        description="Target delegatee reservoir registry and its remote registry to scan.",
    )
    limit: int = Field(
        description="Maximum number of artifacts to scan.",
    )
    artifact_type: ArtifactType | None = Field(
        default=None,
        description="Filter artifacts by type.",
    )
    search: str | None = Field(
        default=None,
        description="Search term to filter artifacts by name or description.",
    )


class DelegateImportArtifactsInput(BaseRequestModel):
    """Input for delegated import of artifact revisions from a reservoir registry."""

    artifact_revision_ids: list[UUID] = Field(
        description="List of artifact revision IDs of delegatee artifact registry.",
    )
    delegator_reservoir_id: UUID | None = Field(
        default=None,
        description="ID of the reservoir registry to delegate the import request to.",
    )
    artifact_type: ArtifactType | None = Field(
        default=None,
        description="Filter artifacts by type.",
    )
    delegatee_target: DelegateeTargetInput | None = Field(
        default=None,
        description="Target delegatee reservoir registry.",
    )
    options: ImportArtifactsOptionsInput | None = Field(
        default=None,
        description="Options controlling import behavior.",
    )


class ModelTargetInput(BaseRequestModel):
    """Specifies a target model for scanning operations."""

    model_id: str = Field(
        description="Model ID in the external registry.",
    )
    revision: str | None = Field(
        default=None,
        description="Specific revision (branch or tag). Defaults to 'main' if not specified.",
    )


class ScanArtifactModelsInput(BaseRequestModel):
    """Input for batch scanning of specific models from external registries."""

    models: list[ModelTargetInput] = Field(
        description="List of model targets to scan.",
    )
    registry_id: UUID | None = Field(
        default=None,
        description="Optional registry ID to scan models from.",
    )


class ArtifactStatusChangedInputDTO(BaseRequestModel):
    """Input for subscribing to artifact status change notifications."""

    artifact_revision_ids: list[UUID] = Field(description="List of artifact revision IDs to watch.")


class ArtifactGQLFilterInputDTO(BaseRequestModel):
    """GQL-facing filter for artifacts."""

    type: list[ArtifactType] | None = Field(default=None)
    name: StringFilter | None = Field(default=None)
    registry: StringFilter | None = Field(default=None)
    source: StringFilter | None = Field(default=None)
    availability: list[ArtifactAvailability] | None = Field(default=None)
    AND: list[ArtifactGQLFilterInputDTO] | None = Field(default=None)
    OR: list[ArtifactGQLFilterInputDTO] | None = Field(default=None)
    NOT: list[ArtifactGQLFilterInputDTO] | None = Field(default=None)


ArtifactGQLFilterInputDTO.model_rebuild()


class ArtifactGQLOrderByInputDTO(BaseRequestModel):
    """GQL-facing order by for artifacts."""

    field: ArtifactOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC)


class ArtifactRevisionStatusFilterDTO(BaseRequestModel):
    """Filter for artifact revision status."""

    in_: list[ArtifactStatus] | None = Field(default=None, alias="in")
    equals: ArtifactStatus | None = Field(default=None)


class ArtifactRevisionRemoteStatusFilterDTO(BaseRequestModel):
    """Filter for artifact revision remote status."""

    in_: list[ArtifactRemoteStatus] | None = Field(default=None, alias="in")
    equals: ArtifactRemoteStatus | None = Field(default=None)


class ArtifactRevisionGQLFilterInputDTO(BaseRequestModel):
    """GQL-facing filter for artifact revisions."""

    status: ArtifactRevisionStatusFilterDTO | None = Field(default=None)
    remote_status: ArtifactRevisionRemoteStatusFilterDTO | None = Field(default=None)
    version: StringFilter | None = Field(default=None)
    artifact_id: UUIDFilter | None = Field(default=None)
    size: IntFilter | None = Field(default=None)
    AND: list[ArtifactRevisionGQLFilterInputDTO] | None = Field(default=None)
    OR: list[ArtifactRevisionGQLFilterInputDTO] | None = Field(default=None)
    NOT: list[ArtifactRevisionGQLFilterInputDTO] | None = Field(default=None)


ArtifactRevisionGQLFilterInputDTO.model_rebuild()


class ArtifactRevisionGQLOrderByInputDTO(BaseRequestModel):
    """GQL-facing order by for artifact revisions."""

    field: ArtifactRevisionOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC)


class AdminSearchArtifactRevisionsInput(BaseRequestModel):
    """Input for searching artifact revisions with GQL filters, orders, and pagination."""

    filter: ArtifactRevisionGQLFilterInputDTO | None = Field(
        default=None, description="Filter conditions."
    )
    order: list[ArtifactRevisionGQLOrderByInputDTO] | None = Field(
        default=None, description="Order specifications."
    )
    # Cursor-based pagination (Relay)
    first: int | None = Field(default=None, ge=1, description="Number of items from the start.")
    after: str | None = Field(default=None, description="Cursor to paginate forward from.")
    last: int | None = Field(default=None, ge=1, description="Number of items from the end.")
    before: str | None = Field(default=None, description="Cursor to paginate backward from.")
    # Offset-based pagination
    limit: int | None = Field(default=None, ge=1, description="Maximum number of items to return.")
    offset: int | None = Field(default=None, ge=0, description="Number of items to skip.")


class AdminSearchArtifactsGQLInput(BaseRequestModel):
    """Input for searching artifacts with GQL filters, orders, and pagination."""

    filter: ArtifactGQLFilterInputDTO | None = Field(default=None, description="Filter conditions.")
    order: list[ArtifactGQLOrderByInputDTO] | None = Field(
        default=None, description="Order specifications."
    )
    # Cursor-based pagination (Relay)
    first: int | None = Field(default=None, ge=1, description="Number of items from the start.")
    after: str | None = Field(default=None, description="Cursor to paginate forward from.")
    last: int | None = Field(default=None, ge=1, description="Number of items from the end.")
    before: str | None = Field(default=None, description="Cursor to paginate backward from.")
    # Offset-based pagination
    limit: int | None = Field(default=None, ge=1, description="Maximum number of items to return.")
    offset: int | None = Field(default=None, ge=0, description="Number of items to skip.")


class UpdateArtifactGQLInput(BaseRequestModel):
    """GQL input for updating artifact metadata."""

    artifact_id: UUID = Field(description="ID of the artifact to update.")
    readonly: bool | None = Field(
        default=None, description="Whether the artifact should be readonly."
    )
    description: str | None = Field(default=None, description="Updated description.")
