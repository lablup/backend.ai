"""
Request DTOs for Storage Backend DTO v2.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.common import String64
from ai.backend.common.tristate.unset import UNSET, Unset

from .types import (
    OrderDirection,
    ServiceStorageBackendStatusOrderField,
    StorageBackendOrderField,
)

__all__ = (
    "AdminSearchStorageBackendsInput",
    "SearchServiceStorageBackendStatusesInput",
    "ServiceStorageBackendStatusFilter",
    "ServiceStorageBackendStatusOrder",
    "StorageBackendFilter",
    "StorageBackendOrder",
    "UpdateStorageBackendInput",
)


class StorageBackendFilter(BaseRequestModel):
    """Filter conditions for a storage backend search."""

    entity_id: UUIDFilter | None = Field(default=None, description="Filter by backend ID.")
    name: StringFilter | None = Field(default=None, description="Filter by backend name.")
    storage_backend_type_id: UUIDFilter | None = Field(
        default=None, description="Filter by the backend implementation's ID."
    )
    AND: list[StorageBackendFilter] | None = Field(
        default=None, description="Logical AND of multiple filter conditions."
    )
    OR: list[StorageBackendFilter] | None = Field(
        default=None, description="Logical OR of multiple filter conditions."
    )
    NOT: list[StorageBackendFilter] | None = Field(
        default=None, description="Logical NOT of filter conditions."
    )


StorageBackendFilter.model_rebuild()


class StorageBackendOrder(BaseRequestModel):
    """Order specification for a storage backend search."""

    field: StorageBackendOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction.")


class AdminSearchStorageBackendsInput(BaseRequestModel):
    """Input for searching storage backends.

    Supports two pagination modes (mutually exclusive):
    - Cursor-based: first/after (forward) or last/before (backward)
    - Offset-based: limit/offset
    """

    filter: StorageBackendFilter | None = Field(default=None, description="Filter conditions.")
    order: list[StorageBackendOrder] | None = Field(
        default=None, description="Order specifications."
    )
    first: int | None = Field(default=None, ge=1, description="Number of items from the start.")
    after: str | None = Field(default=None, description="Cursor to paginate forward from.")
    last: int | None = Field(default=None, ge=1, description="Number of items from the end.")
    before: str | None = Field(default=None, description="Cursor to paginate backward from.")
    limit: int | None = Field(default=None, ge=1, description="Maximum number of items to return.")
    offset: int | None = Field(default=None, ge=0, description="Number of items to skip.")


class UpdateStorageBackendInput(BaseRequestModel):
    """Input for updating the metadata an administrator owns on a backend."""

    name: String64 | None | Unset = Field(
        default=UNSET,
        description="Updated backend name. Omit to leave unchanged.",
    )


class ServiceStorageBackendStatusFilter(BaseRequestModel):
    """Filter conditions for the per-service status rows of a backend."""

    service_catalog_id: UUIDFilter | None = Field(
        default=None, description="Filter by the reporting service's ID."
    )
    storage_backend_id: UUIDFilter | None = Field(
        default=None, description="Filter by the reported backend's ID."
    )
    AND: list[ServiceStorageBackendStatusFilter] | None = Field(
        default=None, description="Logical AND of multiple filter conditions."
    )
    OR: list[ServiceStorageBackendStatusFilter] | None = Field(
        default=None, description="Logical OR of multiple filter conditions."
    )
    NOT: list[ServiceStorageBackendStatusFilter] | None = Field(
        default=None, description="Logical NOT of filter conditions."
    )


ServiceStorageBackendStatusFilter.model_rebuild()


class ServiceStorageBackendStatusOrder(BaseRequestModel):
    """Order specification for the per-service status rows of a backend."""

    field: ServiceStorageBackendStatusOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction.")


class SearchServiceStorageBackendStatusesInput(BaseRequestModel):
    """Input for searching the per-service status rows of the backends."""

    filter: ServiceStorageBackendStatusFilter | None = Field(
        default=None, description="Filter conditions."
    )
    order: list[ServiceStorageBackendStatusOrder] | None = Field(
        default=None, description="Order specifications."
    )
    first: int | None = Field(default=None, ge=1, description="Number of items from the start.")
    after: str | None = Field(default=None, description="Cursor to paginate forward from.")
    last: int | None = Field(default=None, ge=1, description="Number of items from the end.")
    before: str | None = Field(default=None, description="Cursor to paginate backward from.")
    limit: int | None = Field(default=None, ge=1, description="Maximum number of items to return.")
    offset: int | None = Field(default=None, ge=0, description="Number of items to skip.")
