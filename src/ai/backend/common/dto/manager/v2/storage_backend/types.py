"""
Common types for Storage Backend DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.dto.manager.v2.common import OrderDirection

__all__ = (
    "OrderDirection",
    "ServiceStorageBackendStatusOrderField",
    "StorageBackendOrderField",
)


class StorageBackendOrderField(StrEnum):
    """Fields available for ordering storage backends."""

    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class ServiceStorageBackendStatusOrderField(StrEnum):
    """Fields available for ordering the per-service status rows of a backend."""

    SERVICE_CATALOG_ID = "service_catalog_id"
    STORAGE_BACKEND_ID = "storage_backend_id"
    STATUS_CHECKED_AT = "status_checked_at"
    UPDATED_AT = "updated_at"
