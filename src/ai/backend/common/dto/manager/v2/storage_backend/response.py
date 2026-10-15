"""
Response DTOs for Storage Backend DTO v2.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "AdminSearchStorageBackendsPayload",
    "GetStorageBackendPayload",
    "PurgeStorageBackendPayload",
    "SearchServiceStorageBackendStatusesPayload",
    "ServiceStorageBackendStatusNode",
    "StorageBackendNode",
    "UpdateStorageBackendPayload",
)


class StorageBackendNode(BaseResponseModel):
    """Node model representing a storage backend.

    How the appliance is reached is the holding service's own configuration and is
    never returned.
    """

    id: UUID = Field(description="Storage backend ID")
    entity_id: UUID = Field(description="UUID of the storage backend")
    name: str = Field(description="Storage backend name")
    storage_backend_type_id: UUID = Field(
        description="ID of the backend implementation serving this appliance"
    )
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class ServiceStorageBackendStatusNode(BaseResponseModel):
    """Node model representing a storage backend as one service last reported it."""

    service_catalog_id: UUID = Field(description="ID of the reporting service")
    storage_backend_id: UUID = Field(description="ID of the reported storage backend")
    status_checked_at: datetime | None = Field(
        description="When the reporting service last checked the backend"
    )
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class GetStorageBackendPayload(BaseResponseModel):
    """Payload for a single storage backend read."""

    item: StorageBackendNode = Field(description="The storage backend read.")


class AdminSearchStorageBackendsPayload(BaseResponseModel):
    """Payload for a storage backend search."""

    items: list[StorageBackendNode] = Field(description="List of matching storage backends.")
    total_count: int = Field(description="Total number of matching backends.")
    has_next_page: bool = Field(description="Whether there are more items after this page.")
    has_previous_page: bool = Field(description="Whether there are more items before this page.")


class UpdateStorageBackendPayload(BaseResponseModel):
    """Payload for a storage backend update."""

    item: StorageBackendNode = Field(description="The updated storage backend.")


class PurgeStorageBackendPayload(BaseResponseModel):
    """Payload for a storage backend purge."""

    id: UUID = Field(description="ID of the purged storage backend")


class SearchServiceStorageBackendStatusesPayload(BaseResponseModel):
    """Payload for a search over the per-service status rows of the backends."""

    items: list[ServiceStorageBackendStatusNode] = Field(
        description="List of matching status rows."
    )
    total_count: int = Field(description="Total number of matching status rows.")
    has_next_page: bool = Field(description="Whether there are more items after this page.")
    has_previous_page: bool = Field(description="Whether there are more items before this page.")
