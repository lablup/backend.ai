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
    "SearchStorageVolumeServiceAttachmentsPayload",
    "SearchStorageVolumesPayload",
    "StorageVolumeNode",
    "StorageVolumeServiceAttachmentNode",
    "UpdateStorageVolumePayload",
)


class StorageVolumeNode(BaseResponseModel):
    """Node model representing a storage volume.

    Carries no status: what each service sees is read through its attachments.
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


class StorageVolumeServiceAttachmentNode(BaseResponseModel):
    """Node model representing a storage volume as one service has it attached."""

    id: UUID = Field(description="Storage volume service attachment ID")
    service_catalog_id: UUID = Field(description="ID of the service the volume is attached to")
    storage_volume_id: UUID = Field(description="ID of the attached volume")
    status_checked_at: datetime | None = Field(
        description="When the service last checked the volume"
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


class SearchStorageVolumeServiceAttachmentsPayload(BaseResponseModel):
    """Payload for a search over the storage volume service attachments."""

    items: list[StorageVolumeServiceAttachmentNode] = Field(
        description="List of matching storage volume service attachments."
    )
    total_count: int = Field(
        description="Total number of matching storage volume service attachments."
    )
    has_next_page: bool = Field(description="Whether there are more items after this page.")
    has_previous_page: bool = Field(description="Whether there are more items before this page.")


class DeleteStorageVolumePayload(BaseResponseModel):
    """Payload for a storage volume soft delete."""

    item: StorageVolumeNode = Field(description="The withdrawn storage volume.")


class RestoreStorageVolumePayload(BaseResponseModel):
    """Payload for a storage volume restore."""

    item: StorageVolumeNode = Field(description="The restored storage volume.")
