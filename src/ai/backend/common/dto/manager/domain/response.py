"""
Response DTOs for domain management.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "CreateDomainResponse",
    "DeleteDomainResponse",
    "DomainDTO",
    "GetDomainResponse",
    "PaginationInfo",
    "PurgeDomainResponse",
    "SearchDomainsResponse",
    "UpdateDomainResponse",
)


class DomainDTO(BaseModel):
    """DTO for domain data."""

    name: str = Field(description="Domain name (primary key)")
    description: str | None = Field(default=None, description="Domain description")
    is_active: bool = Field(description="Whether the domain is active")
    created_at: datetime = Field(description="Creation timestamp")
    modified_at: datetime = Field(description="Last modification timestamp")
    total_resource_slots: dict[str, Any] = Field(description="Total resource slots")
    allowed_vfolder_hosts: dict[str, Any] = Field(
        description="Allowed vfolder hosts with permissions"
    )
    allowed_docker_registries: list[str] = Field(description="Allowed docker registries")
    integration_id: str | None = Field(default=None, description="External integration ID")


class PaginationInfo(BaseModel):
    """Pagination information."""

    total: int = Field(description="Total number of items")
    offset: int = Field(description="Number of items skipped")
    limit: int | None = Field(default=None, description="Maximum items returned")


class CreateDomainResponse(BaseResponseModel):
    """Response for creating a domain."""

    domain: DomainDTO = Field(description="Created domain")


class GetDomainResponse(BaseResponseModel):
    """Response for getting a domain."""

    domain: DomainDTO = Field(description="Domain data")


class SearchDomainsResponse(BaseResponseModel):
    """Response for searching domains."""

    domains: list[DomainDTO] = Field(description="List of domains")
    pagination: PaginationInfo = Field(description="Pagination information")


class UpdateDomainResponse(BaseResponseModel):
    """Response for updating a domain."""

    domain: DomainDTO = Field(description="Updated domain")


class DeleteDomainResponse(BaseResponseModel):
    """Response for deleting a domain."""

    deleted: bool = Field(description="Whether the domain was deleted")


class PurgeDomainResponse(BaseResponseModel):
    """Response for purging a domain."""

    purged: bool = Field(description="Whether the domain was purged")
