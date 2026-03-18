"""Request DTOs for Resource Usage DTO v2."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = (
    "AdminSearchDomainUsageBucketsInput",
    "AdminSearchProjectUsageBucketsInput",
    "AdminSearchUserUsageBucketsInput",
    "DomainSearchDomainUsageBucketsInput",
    "DomainSearchProjectUsageBucketsInput",
    "DomainSearchUserUsageBucketsInput",
)


class AdminSearchDomainUsageBucketsInput(BaseRequestModel):
    """Input for admin search of domain usage buckets (no scope)."""

    domain_name: str | None = Field(default=None, description="Filter by domain name")
    resource_group: str | None = Field(default=None, description="Filter by resource group")
    limit: int | None = Field(default=None, ge=1, description="Max results per page")
    offset: int | None = Field(default=None, ge=0, description="Pagination offset")


class AdminSearchProjectUsageBucketsInput(BaseRequestModel):
    """Input for admin search of project usage buckets (no scope)."""

    domain_name: str | None = Field(default=None, description="Filter by domain name")
    resource_group: str | None = Field(default=None, description="Filter by resource group")
    project_id: UUID | None = Field(default=None, description="Filter by project ID")
    limit: int | None = Field(default=None, ge=1, description="Max results per page")
    offset: int | None = Field(default=None, ge=0, description="Pagination offset")


class AdminSearchUserUsageBucketsInput(BaseRequestModel):
    """Input for admin search of user usage buckets (no scope)."""

    domain_name: str | None = Field(default=None, description="Filter by domain name")
    resource_group: str | None = Field(default=None, description="Filter by resource group")
    project_id: UUID | None = Field(default=None, description="Filter by project ID")
    user_uuid: UUID | None = Field(default=None, description="Filter by user UUID")
    limit: int | None = Field(default=None, ge=1, description="Max results per page")
    offset: int | None = Field(default=None, ge=0, description="Pagination offset")


class DomainSearchDomainUsageBucketsInput(BaseRequestModel):
    """Input for scoped search of domain usage buckets within a domain/resource-group."""

    domain_name: str = Field(description="Domain name scope")
    resource_group: str = Field(description="Resource group scope")
    limit: int | None = Field(default=None, ge=1, description="Max results per page")
    offset: int | None = Field(default=None, ge=0, description="Pagination offset")


class DomainSearchProjectUsageBucketsInput(BaseRequestModel):
    """Input for scoped search of project usage buckets within a domain/resource-group."""

    domain_name: str = Field(description="Domain name scope")
    resource_group: str = Field(description="Resource group scope")
    project_id: UUID = Field(description="Project ID scope")
    limit: int | None = Field(default=None, ge=1, description="Max results per page")
    offset: int | None = Field(default=None, ge=0, description="Pagination offset")


class DomainSearchUserUsageBucketsInput(BaseRequestModel):
    """Input for scoped search of user usage buckets within a domain/resource-group."""

    domain_name: str = Field(description="Domain name scope")
    resource_group: str = Field(description="Resource group scope")
    project_id: UUID = Field(description="Project ID scope")
    user_uuid: UUID = Field(description="User UUID scope")
    limit: int | None = Field(default=None, ge=1, description="Max results per page")
    offset: int | None = Field(default=None, ge=0, description="Pagination offset")
