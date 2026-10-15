"""
Request DTOs for Storage Volume DTO v2.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.common import String64
from ai.backend.common.tristate.unset import UNSET, Unset

from .types import (
    OrderDirection,
    ResourceGroupVolumeOfferOrderField,
    StorageVolumeOrderField,
    StorageVolumeServiceHoldingOrderField,
    StorageVolumeUsageExposureInput,
)

__all__ = (
    "AdminSearchStorageVolumesInput",
    "PurgeResourceGroupVolumeOfferInput",
    "UpsertResourceGroupVolumeOfferInput",
    "ResourceGroupVolumeOfferFilter",
    "ResourceGroupVolumeOfferOrder",
    "SearchResourceGroupVolumeOffersInput",
    "SearchStorageVolumeServiceHoldingsInput",
    "StorageVolumeFilter",
    "StorageVolumeOrder",
    "StorageVolumeServiceHoldingFilter",
    "StorageVolumeServiceHoldingOrder",
    "UpdateStorageVolumeInput",
)


class StorageVolumeFilter(BaseRequestModel):
    """Filter conditions for a storage volume search."""

    entity_id: UUIDFilter | None = Field(default=None, description="Filter by volume ID.")
    name: StringFilter | None = Field(default=None, description="Filter by volume name.")
    storage_backend_id: UUIDFilter | None = Field(
        default=None, description="Filter by the backend the volume sits on."
    )
    AND: list[StorageVolumeFilter] | None = Field(
        default=None, description="Logical AND of multiple filter conditions."
    )
    OR: list[StorageVolumeFilter] | None = Field(
        default=None, description="Logical OR of multiple filter conditions."
    )
    NOT: list[StorageVolumeFilter] | None = Field(
        default=None, description="Logical NOT of filter conditions."
    )


StorageVolumeFilter.model_rebuild()


class StorageVolumeOrder(BaseRequestModel):
    """Order specification for a storage volume search."""

    field: StorageVolumeOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction.")


class AdminSearchStorageVolumesInput(BaseRequestModel):
    """Input for searching storage volumes.

    Supports two pagination modes (mutually exclusive):
    - Cursor-based: first/after (forward) or last/before (backward)
    - Offset-based: limit/offset
    """

    filter: StorageVolumeFilter | None = Field(default=None, description="Filter conditions.")
    order: list[StorageVolumeOrder] | None = Field(
        default=None, description="Order specifications."
    )
    first: int | None = Field(default=None, ge=1, description="Number of items from the start.")
    after: str | None = Field(default=None, description="Cursor to paginate forward from.")
    last: int | None = Field(default=None, ge=1, description="Number of items from the end.")
    before: str | None = Field(default=None, description="Cursor to paginate backward from.")
    limit: int | None = Field(default=None, ge=1, description="Maximum number of items to return.")
    offset: int | None = Field(default=None, ge=0, description="Number of items to skip.")


class UpdateStorageVolumeInput(BaseRequestModel):
    """Input for updating the metadata an administrator owns on a volume."""

    name: String64 | None | Unset = Field(
        default=UNSET,
        description="Updated volume name. Omit to leave unchanged.",
    )
    status_stale_after_seconds: int | None | Unset = Field(
        default=UNSET,
        ge=1,
        description=(
            "How long the volume may go without a fresh check before it counts as stale."
            " Omit to leave unchanged."
        ),
    )
    usage_exposure: StorageVolumeUsageExposureInput | None | Unset = Field(
        default=UNSET,
        description="Updated usage exposure. Omit to leave unchanged.",
    )


class StorageVolumeServiceHoldingFilter(BaseRequestModel):
    """Filter conditions for the per-service holdings of a volume."""

    service_catalog_id: UUIDFilter | None = Field(
        default=None, description="Filter by the holding service's ID."
    )
    storage_volume_id: UUIDFilter | None = Field(
        default=None, description="Filter by the held volume's ID."
    )
    AND: list[StorageVolumeServiceHoldingFilter] | None = Field(
        default=None, description="Logical AND of multiple filter conditions."
    )
    OR: list[StorageVolumeServiceHoldingFilter] | None = Field(
        default=None, description="Logical OR of multiple filter conditions."
    )
    NOT: list[StorageVolumeServiceHoldingFilter] | None = Field(
        default=None, description="Logical NOT of filter conditions."
    )


StorageVolumeServiceHoldingFilter.model_rebuild()


class StorageVolumeServiceHoldingOrder(BaseRequestModel):
    """Order specification for the per-service holdings of a volume."""

    field: StorageVolumeServiceHoldingOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction.")


class SearchStorageVolumeServiceHoldingsInput(BaseRequestModel):
    """Input for searching which services hold which volumes."""

    filter: StorageVolumeServiceHoldingFilter | None = Field(
        default=None, description="Filter conditions."
    )
    order: list[StorageVolumeServiceHoldingOrder] | None = Field(
        default=None, description="Order specifications."
    )
    first: int | None = Field(default=None, ge=1, description="Number of items from the start.")
    after: str | None = Field(default=None, description="Cursor to paginate forward from.")
    last: int | None = Field(default=None, ge=1, description="Number of items from the end.")
    before: str | None = Field(default=None, description="Cursor to paginate backward from.")
    limit: int | None = Field(default=None, ge=1, description="Maximum number of items to return.")
    offset: int | None = Field(default=None, ge=0, description="Number of items to skip.")


class ResourceGroupVolumeOfferFilter(BaseRequestModel):
    """Filter conditions for the offers of a volume to resource groups."""

    resource_group_id: UUIDFilter | None = Field(
        default=None, description="Filter by the resource group offered to."
    )
    storage_volume_id: UUIDFilter | None = Field(
        default=None, description="Filter by the offered volume's ID."
    )
    enabled: bool | None = Field(
        default=None, description="Filter by whether the offer is enabled."
    )
    is_default: bool | None = Field(
        default=None, description="Filter by whether the offer is the resource group's default."
    )
    AND: list[ResourceGroupVolumeOfferFilter] | None = Field(
        default=None, description="Logical AND of multiple filter conditions."
    )
    OR: list[ResourceGroupVolumeOfferFilter] | None = Field(
        default=None, description="Logical OR of multiple filter conditions."
    )
    NOT: list[ResourceGroupVolumeOfferFilter] | None = Field(
        default=None, description="Logical NOT of filter conditions."
    )


ResourceGroupVolumeOfferFilter.model_rebuild()


class ResourceGroupVolumeOfferOrder(BaseRequestModel):
    """Order specification for the offers of a volume to resource groups."""

    field: ResourceGroupVolumeOfferOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction.")


class SearchResourceGroupVolumeOffersInput(BaseRequestModel):
    """Input for searching which volumes are offered to which resource groups."""

    filter: ResourceGroupVolumeOfferFilter | None = Field(
        default=None, description="Filter conditions."
    )
    order: list[ResourceGroupVolumeOfferOrder] | None = Field(
        default=None, description="Order specifications."
    )
    first: int | None = Field(default=None, ge=1, description="Number of items from the start.")
    after: str | None = Field(default=None, description="Cursor to paginate forward from.")
    last: int | None = Field(default=None, ge=1, description="Number of items from the end.")
    before: str | None = Field(default=None, description="Cursor to paginate backward from.")
    limit: int | None = Field(default=None, ge=1, description="Maximum number of items to return.")
    offset: int | None = Field(default=None, ge=0, description="Number of items to skip.")


class UpsertResourceGroupVolumeOfferInput(BaseRequestModel):
    """Input for offering a volume to a resource group, or for retuning an offer.

    The pair is the key: offering a volume already offered rewrites the flags it
    carries. At most one offer per resource group may be the default.
    """

    resource_group_id: UUID = Field(description="The resource group the volume is offered to.")
    storage_volume_id: UUID = Field(description="The volume being offered.")
    enabled: bool | None | Unset = Field(
        default=UNSET,
        description="Whether the offer is enabled. Defaults to true on a new offer.",
    )
    is_default: bool | None | Unset = Field(
        default=UNSET,
        description=(
            "Whether the offer is the resource group's default. Defaults to false on a new offer."
        ),
    )


class PurgeResourceGroupVolumeOfferInput(BaseRequestModel):
    """Input for withdrawing a volume from a resource group."""

    resource_group_id: UUID = Field(description="The resource group the volume was offered to.")
    storage_volume_id: UUID = Field(description="The volume being withdrawn.")
