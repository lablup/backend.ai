"""
Request DTOs for Service Catalog DTO v2.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.tristate.unset import UNSET, Unset
from ai.backend.common.types import ServiceCatalogStatus

from .types import OrderDirection, ServiceCatalogOrderField, ServiceCatalogStatusFilter

__all__ = (
    "AdminSearchServiceCatalogsInput",
    "CreateServiceCatalogInput",
    "DeleteServiceCatalogInput",
    "EndpointInput",
    "HeartbeatInput",
    "ServiceCatalogFilter",
    "ServiceCatalogOrder",
    "UpdateServiceCatalogInput",
)


class EndpointInput(BaseRequestModel):
    """Input for a service catalog endpoint."""

    role: str = Field(min_length=1, max_length=32, description="Role of the endpoint")
    scope: str = Field(min_length=1, max_length=32, description="Scope of the endpoint")
    address: str = Field(
        min_length=1, max_length=256, description="Network address of the endpoint"
    )
    port: int = Field(ge=1, le=65535, description="Port number of the endpoint")
    protocol: str = Field(min_length=1, max_length=16, description="Protocol used by the endpoint")
    metadata: dict[str, Any] | None = Field(
        default=None, description="Optional metadata for the endpoint"
    )


class CreateServiceCatalogInput(BaseRequestModel):
    """Input for registering a new service catalog entry."""

    service_group: str = Field(
        min_length=1,
        max_length=64,
        description="Service group identifier",
    )
    instance_id: str = Field(
        min_length=1,
        max_length=128,
        description="Unique instance identifier within the service group",
    )
    display_name: str = Field(
        min_length=1,
        max_length=256,
        description="Human-readable display name for the service",
    )
    version: str = Field(
        min_length=1,
        max_length=64,
        description="Version string of the service",
    )
    labels: dict[str, Any] = Field(
        default_factory=dict,
        description="Key-value labels for the service",
    )
    status: ServiceCatalogStatus = Field(description="Current status of the service")
    startup_time: datetime = Field(description="Time when the service started")
    config_hash: str = Field(default="", description="Hash of the service configuration")
    endpoints: list[EndpointInput] | None = Field(
        default=None, description="List of endpoints exposed by the service"
    )

    @field_validator("display_name")
    @classmethod
    def display_name_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("display_name must not be blank or whitespace-only")
        return stripped


class UpdateServiceCatalogInput(BaseRequestModel):
    """Input for updating an existing service catalog entry."""

    display_name: str | None | Unset = Field(
        default=UNSET,
        description="Updated display name. Omit to leave unchanged.",
    )
    version: str | None | Unset = Field(
        default=UNSET, description="Updated version string. Omit to leave unchanged."
    )
    labels: dict[str, Any] | None | Unset = Field(
        default=UNSET, description="Updated labels. Omit to leave unchanged; null clears."
    )
    status: ServiceCatalogStatus | None | Unset = Field(
        default=UNSET, description="Updated service status. Omit to leave unchanged."
    )
    config_hash: str | None | Unset = Field(
        default=UNSET, description="Updated configuration hash. Omit to leave unchanged."
    )

    @field_validator("display_name")
    @classmethod
    def display_name_must_not_be_blank(cls, v: str | None | Unset) -> str | None | Unset:
        if not isinstance(v, str):
            return v
        stripped = v.strip()
        if not stripped:
            raise ValueError("display_name must not be blank or whitespace-only")
        return stripped


class DeleteServiceCatalogInput(BaseRequestModel):
    """Input for deleting a service catalog entry."""

    id: UUID = Field(description="Service catalog entry ID to delete")


class HeartbeatInput(BaseRequestModel):
    """Input for updating the heartbeat of a service catalog entry."""

    id: UUID = Field(description="Service catalog entry ID to heartbeat")


class ServiceCatalogFilter(BaseRequestModel):
    """Filter conditions for service catalog search."""

    service_group: StringFilter | None = Field(
        default=None, description="Filter by service group name."
    )
    status: ServiceCatalogStatusFilter | None = Field(
        default=None, description="Filter by health status."
    )
    AND: list[ServiceCatalogFilter] | None = Field(
        default=None, description="Logical AND of multiple filter conditions."
    )
    OR: list[ServiceCatalogFilter] | None = Field(
        default=None, description="Logical OR of multiple filter conditions."
    )
    NOT: list[ServiceCatalogFilter] | None = Field(
        default=None, description="Logical NOT of filter conditions."
    )


ServiceCatalogFilter.model_rebuild()


class ServiceCatalogOrder(BaseRequestModel):
    """Order specification for service catalog search."""

    field: ServiceCatalogOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction.")


class AdminSearchServiceCatalogsInput(BaseRequestModel):
    """Input for searching service catalog entries with filters, orders, and pagination.

    Supports two pagination modes (mutually exclusive):
    - Cursor-based: first/after (forward) or last/before (backward)
    - Offset-based: limit/offset
    """

    filter: ServiceCatalogFilter | None = Field(default=None, description="Filter conditions.")
    order: list[ServiceCatalogOrder] | None = Field(
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


ServiceCatalogFilter.model_rebuild()
