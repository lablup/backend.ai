"""
Request DTOs for Domain v2 admin REST API.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel
from ai.backend.common.dto.manager.defs import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.domain.types import DomainOrderField, OrderDirection

__all__ = (
    "CreateDomainInput",
    "DeleteDomainInput",
    "DomainFilter",
    "DomainOrder",
    "PurgeDomainInput",
    "SearchDomainsRequest",
    "UpdateDomainInput",
)


class CreateDomainInput(BaseRequestModel):
    """Input for creating a new domain."""

    name: str = Field(
        description="Domain name. Must be unique across the system.",
        max_length=64,
    )
    description: str | None = Field(
        default=None,
        description="Optional description of the domain.",
    )
    is_active: bool = Field(
        default=True,
        description="Whether the domain is active upon creation.",
    )
    allowed_docker_registries: list[str] | None = Field(
        default=None,
        description="List of allowed Docker registry URLs for this domain.",
    )
    integration_id: str | None = Field(
        default=None,
        description="External integration identifier for the domain.",
    )


class UpdateDomainInput(BaseRequestModel):
    """Input for updating domain information. All fields optional — only provided fields will be updated."""

    name: str | None = Field(
        default=None,
        description="New domain name.",
        max_length=64,
    )
    description: str | Sentinel | None = Field(
        default=SENTINEL,
        description="New domain description. Set to null to clear.",
    )
    is_active: bool | None = Field(
        default=None,
        description="Updated active status.",
    )
    allowed_docker_registries: list[str] | Sentinel | None = Field(
        default=SENTINEL,
        description="New list of allowed Docker registry URLs. Set to null to clear.",
    )
    integration_id: str | Sentinel | None = Field(
        default=SENTINEL,
        description="New external integration identifier. Set to null to clear.",
    )


class DeleteDomainInput(BaseRequestModel):
    """Input for soft-deleting a domain."""

    name: str = Field(description="Name of the domain to soft-delete.")


class PurgeDomainInput(BaseRequestModel):
    """Input for permanently purging a domain and all associated data."""

    name: str = Field(description="Name of the domain to permanently purge.")


class DomainFilter(BaseRequestModel):
    """Filter criteria for searching domains."""

    name: StringFilter | None = Field(default=None, description="Filter by domain name.")
    is_active: bool | None = Field(default=None, description="Filter by active status.")


class DomainOrder(BaseRequestModel):
    """Order specification for domain search results."""

    field: DomainOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(
        default=OrderDirection.ASC,
        description="Order direction.",
    )


class SearchDomainsRequest(BaseRequestModel):
    """Request body for searching domains with filters, orders, and pagination."""

    filter: DomainFilter | None = Field(default=None, description="Filter conditions.")
    order: list[DomainOrder] | None = Field(default=None, description="Order specifications.")
    limit: int = Field(
        default=DEFAULT_PAGE_LIMIT,
        ge=1,
        le=MAX_PAGE_LIMIT,
        description="Maximum items to return.",
    )
    offset: int = Field(default=0, ge=0, description="Number of items to skip.")
