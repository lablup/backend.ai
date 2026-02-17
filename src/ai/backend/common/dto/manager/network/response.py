"""
Response DTOs for network system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "CreateNetworkResponse",
    "DeleteNetworkResponse",
    "GetNetworkResponse",
    "NetworkDTO",
    "PaginationInfo",
    "SearchNetworksResponse",
    "UpdateNetworkResponse",
)


class NetworkDTO(BaseModel):
    """DTO for network data."""

    id: UUID = Field(description="Network ID")
    name: str = Field(description="Network name")
    ref_name: str = Field(description="Network reference name from plugin")
    driver: str = Field(description="Network driver plugin name")
    options: dict[str, Any] = Field(description="Network options from plugin")
    project: UUID = Field(description="Associated project (group) ID")
    domain_name: str = Field(description="Associated domain name")
    created_at: datetime | None = Field(default=None, description="Creation timestamp")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp")


class PaginationInfo(BaseModel):
    """Pagination information."""

    total: int = Field(description="Total number of items")
    offset: int = Field(description="Number of items skipped")
    limit: int | None = Field(default=None, description="Maximum items returned")


class CreateNetworkResponse(BaseResponseModel):
    """Response for creating a network."""

    network: NetworkDTO = Field(description="Created network")


class GetNetworkResponse(BaseResponseModel):
    """Response for getting a network."""

    network: NetworkDTO = Field(description="Network data")


class SearchNetworksResponse(BaseResponseModel):
    """Response for searching networks."""

    items: list[NetworkDTO] = Field(description="List of networks")
    pagination: PaginationInfo = Field(description="Pagination information")


class UpdateNetworkResponse(BaseResponseModel):
    """Response for updating a network."""

    network: NetworkDTO = Field(description="Updated network")


class DeleteNetworkResponse(BaseResponseModel):
    """Response for deleting a network."""

    deleted: bool = Field(description="Whether the network was deleted")
