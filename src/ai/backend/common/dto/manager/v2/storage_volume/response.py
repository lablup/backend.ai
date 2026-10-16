"""
Response DTOs for Storage Volume DTO v2.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.storage_volume.types import StorageVolumeUsageExposureInfo

__all__ = (
    "AdminSearchStorageVolumesPayload",
    "DeleteStorageVolumePayload",
    "RestoreStorageVolumePayload",
    "PurgeResourceGroupVolumeOfferPayload",
    "UpsertResourceGroupVolumeOfferPayload",
    "GetStorageVolumePayload",
    "PurgeStorageVolumePayload",
    "ResourceGroupVolumeOfferNode",
    "SearchResourceGroupVolumeOffersPayload",
    "SearchStorageVolumeServiceHoldingsPayload",
    "StorageVolumeNode",
    "StorageVolumeServiceHoldingNode",
    "UpdateStorageVolumePayload",
)


class StorageVolumeNode(BaseResponseModel):
    """Node model representing a storage volume.

    Carries no status: what each service sees is read through its holdings.
    """

    id: UUID = Field(description="Storage volume ID")
    entity_id: UUID = Field(description="UUID of the storage volume")
    name: str = Field(description="Volume name, as every service declares it")
    storage_backend_id: UUID = Field(description="ID of the backend the volume sits on")
    status_stale_after_seconds: int = Field(
        description="How long the volume may go without a fresh check before it counts as stale"
    )
    usage_exposure: StorageVolumeUsageExposureInfo = Field(
        description="Which usage figures the volume shows a user"
    )
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class StorageVolumeServiceHoldingNode(BaseResponseModel):
    """Node model representing a storage volume as one service holds it."""

    service_catalog_id: UUID = Field(description="ID of the holding service")
    storage_volume_id: UUID = Field(description="ID of the held volume")
    status_checked_at: datetime | None = Field(
        description="When the holding service last checked the volume"
    )
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class ResourceGroupVolumeOfferNode(BaseResponseModel):
    """Node model representing a storage volume offered to a resource group."""

    resource_group_id: UUID = Field(description="ID of the resource group offered to")
    storage_volume_id: UUID = Field(description="ID of the offered volume")
    enabled: bool = Field(description="Whether the offer is enabled")
    is_default: bool = Field(description="Whether the offer is the resource group's default")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class GetStorageVolumePayload(BaseResponseModel):
    """Payload for a single storage volume read."""

    item: StorageVolumeNode = Field(description="The storage volume read.")


class AdminSearchStorageVolumesPayload(BaseResponseModel):
    """Payload for a storage volume search."""

    items: list[StorageVolumeNode] = Field(description="List of matching storage volumes.")
    total_count: int = Field(description="Total number of matching volumes.")
    has_next_page: bool = Field(description="Whether there are more items after this page.")
    has_previous_page: bool = Field(description="Whether there are more items before this page.")


class UpdateStorageVolumePayload(BaseResponseModel):
    """Payload for a storage volume update."""

    item: StorageVolumeNode = Field(description="The updated storage volume.")


class PurgeStorageVolumePayload(BaseResponseModel):
    """Payload for a storage volume purge."""

    id: UUID = Field(description="ID of the purged storage volume")


class SearchStorageVolumeServiceHoldingsPayload(BaseResponseModel):
    """Payload for a search over the per-service holdings of the volumes."""

    items: list[StorageVolumeServiceHoldingNode] = Field(description="List of matching holdings.")
    total_count: int = Field(description="Total number of matching holdings.")
    has_next_page: bool = Field(description="Whether there are more items after this page.")
    has_previous_page: bool = Field(description="Whether there are more items before this page.")


class SearchResourceGroupVolumeOffersPayload(BaseResponseModel):
    """Payload for a search over the offers of the volumes to resource groups."""

    items: list[ResourceGroupVolumeOfferNode] = Field(description="List of matching offers.")
    total_count: int = Field(description="Total number of matching offers.")
    has_next_page: bool = Field(description="Whether there are more items after this page.")
    has_previous_page: bool = Field(description="Whether there are more items before this page.")


class UpsertResourceGroupVolumeOfferPayload(BaseResponseModel):
    """Payload for offering a volume to a resource group."""

    item: ResourceGroupVolumeOfferNode = Field(description="The offer written.")


class PurgeResourceGroupVolumeOfferPayload(BaseResponseModel):
    """Payload for withdrawing a volume from a resource group."""

    resource_group_id: UUID = Field(description="The resource group the volume was offered to.")
    storage_volume_id: UUID = Field(description="The volume withdrawn.")


class DeleteStorageVolumePayload(BaseResponseModel):
    """Payload for a storage volume soft delete."""

    item: StorageVolumeNode = Field(description="The withdrawn storage volume.")


class RestoreStorageVolumePayload(BaseResponseModel):
    """Payload for a storage volume restore."""

    item: StorageVolumeNode = Field(description="The restored storage volume.")
