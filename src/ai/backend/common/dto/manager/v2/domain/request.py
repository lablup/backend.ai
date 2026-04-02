"""
Request DTOs for Domain v2 admin REST API.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel
from ai.backend.common.dto.manager.defs import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT
from ai.backend.common.dto.manager.query import DateTimeFilter, StringFilter
from ai.backend.common.dto.manager.v2.domain.types import (
    DomainOrderField,
    DomainProjectFilter,
    DomainUserFilter,
    OrderDirection,
)

__all__ = (
    "AdminSearchDomainsInput",
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
    integration_name: str | None = Field(
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
    integration_name: str | Sentinel | None = Field(
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
    description: StringFilter | None = Field(default=None, description="Filter by description.")
    is_active: bool | None = Field(default=None, description="Filter by active status.")
    created_at: DateTimeFilter | None = Field(default=None, description="Filter by creation time.")
    modified_at: DateTimeFilter | None = Field(
        default=None, description="Filter by last modification time."
    )
    project: DomainProjectFilter | None = Field(
        default=None, description="Filter by nested project conditions."
    )
    user: DomainUserFilter | None = Field(
        default=None, description="Filter by nested user conditions."
    )
    AND: list[DomainFilter] | None = Field(default=None, description="AND logical combinator.")
    OR: list[DomainFilter] | None = Field(default=None, description="OR logical combinator.")
    NOT: list[DomainFilter] | None = Field(default=None, description="NOT logical combinator.")


DomainFilter.model_rebuild()


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


class AdminSearchDomainsInput(BaseRequestModel):
    """Input for admin search of domains with cursor and offset pagination."""

    filter: DomainFilter | None = Field(default=None, description="Filter conditions.")
    order: list[DomainOrder] | None = Field(default=None, description="Order specifications.")
    first: int | None = Field(default=None, description="Cursor pagination: number of items.")
    after: str | None = Field(default=None, description="Cursor pagination: after cursor.")
    last: int | None = Field(default=None, description="Cursor pagination: last N items.")
    before: str | None = Field(default=None, description="Cursor pagination: before cursor.")
    limit: int | None = Field(default=None, description="Offset pagination: maximum items.")
    offset: int | None = Field(default=None, description="Offset pagination: number to skip.")
