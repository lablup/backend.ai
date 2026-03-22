"""
Request DTOs for domain management.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter

from .types import DomainOrder

__all__ = (
    "CreateDomainRequest",
    "DeleteDomainRequest",
    "DomainFilter",
    "PurgeDomainRequest",
    "SearchDomainsRequest",
    "UpdateDomainRequest",
)


class CreateDomainRequest(BaseRequestModel):
    """Request to create a domain."""

    name: str = Field(description="Domain name", max_length=64)
    description: str | None = Field(default=None, description="Domain description")
    is_active: bool = Field(default=True, description="Whether the domain is active")
    total_resource_slots: dict[str, Any] | None = Field(
        default=None, description="Total resource slots"
    )
    allowed_vfolder_hosts: dict[str, list[str]] | None = Field(
        default=None, description="Allowed vfolder hosts with permissions"
    )
    allowed_docker_registries: list[str] | None = Field(
        default=None, description="Allowed docker registries"
    )
    integration_id: str | None = Field(default=None, description="External integration ID")


class UpdateDomainRequest(BaseRequestModel):
    """Request to update a domain."""

    name: str | None = Field(default=None, description="New domain name", max_length=64)
    description: str | None = Field(default=None, description="Updated description")
    is_active: bool | None = Field(default=None, description="Updated active status")
    total_resource_slots: dict[str, Any] | None = Field(
        default=None, description="Updated total resource slots"
    )
    allowed_vfolder_hosts: dict[str, list[str]] | None = Field(
        default=None, description="Updated allowed vfolder hosts"
    )
    allowed_docker_registries: list[str] | None = Field(
        default=None, description="Updated allowed docker registries"
    )
    integration_id: str | None = Field(default=None, description="Updated integration ID")


class DomainFilter(BaseRequestModel):
    """Filter for domain search."""

    name: StringFilter | None = Field(default=None, description="Filter by name")
    is_active: bool | None = Field(default=None, description="Filter by active status")


class SearchDomainsRequest(BaseRequestModel):
    """Request body for searching domains with filters, orders, and pagination."""

    filter: DomainFilter | None = Field(default=None, description="Filter conditions")
    order: list[DomainOrder] | None = Field(default=None, description="Order specifications")
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class DeleteDomainRequest(BaseRequestModel):
    """Request to delete (soft-delete) a domain."""

    name: str = Field(description="Domain name to delete")


class PurgeDomainRequest(BaseRequestModel):
    """Request to permanently purge a domain."""

    name: str = Field(description="Domain name to purge")
