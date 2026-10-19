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
    "DeleteStorageVolumePayload",
    "GetStorageVolumePayload",
    "PurgeStorageVolumePayload",
    "RestoreStorageVolumePayload",
    "SearchStorageVolumesPayload",
    "StorageVolumeNode",
    "UpdateStorageVolumePayload",
)


class StorageVolumeNode(BaseResponseModel):
    """Node model representing a storage volume."""

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


class GetStorageVolumePayload(BaseResponseModel):
    """Payload for a single storage volume read."""

    item: StorageVolumeNode = Field(description="The storage volume read.")


class SearchStorageVolumesPayload(BaseResponseModel):
    """Payload for a storage volume search, whether an administrator's or a scoped one."""

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


class DeleteStorageVolumePayload(BaseResponseModel):
    """Payload for a storage volume soft delete."""

    item: StorageVolumeNode = Field(description="The withdrawn storage volume.")


class RestoreStorageVolumePayload(BaseResponseModel):
    """Payload for a storage volume restore."""

    item: StorageVolumeNode = Field(description="The restored storage volume.")
