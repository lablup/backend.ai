"""
Request DTOs for network system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter

from .types import (
    NetworkOrderField,
    OrderDirection,
)

__all__ = (
    "CreateNetworkRequest",
    "DeleteNetworkRequest",
    "NetworkFilter",
    "NetworkOrder",
    "SearchNetworksRequest",
    "UpdateNetworkRequest",
)


class CreateNetworkRequest(BaseRequestModel):
    """Request to create a network."""

    name: str = Field(description="Network name")
    project_id: UUID = Field(description="Project (group) ID to associate the network with")
    driver: str | None = Field(default=None, description="Network driver plugin name")


class UpdateNetworkRequest(BaseRequestModel):
    """Request to update a network."""

    name: str | None = Field(default=None, description="Updated network name")


class NetworkFilter(BaseRequestModel):
    """Filter for networks."""

    name: StringFilter | None = Field(default=None, description="Filter by name")
    driver: StringFilter | None = Field(default=None, description="Filter by driver")
    project: UUIDFilter | None = Field(default=None, description="Filter by project ID")
    domain_name: StringFilter | None = Field(default=None, description="Filter by domain name")


class NetworkOrder(BaseRequestModel):
    """Order specification for networks."""

    field: NetworkOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")


class SearchNetworksRequest(BaseRequestModel):
    """Request body for searching networks with filters, orders, and pagination."""

    filter: NetworkFilter | None = Field(default=None, description="Filter conditions")
    order: list[NetworkOrder] | None = Field(default=None, description="Order specifications")
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class DeleteNetworkRequest(BaseRequestModel):
    """Request to delete a network."""

    network_id: UUID = Field(description="Network ID to delete")
