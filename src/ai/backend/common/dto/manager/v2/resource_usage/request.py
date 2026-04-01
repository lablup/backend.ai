"""Request DTOs for Resource Usage DTO v2."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import DateFilter, StringFilter, UUIDFilter

from .types import OrderDirection, UsageBucketOrderField

__all__ = (
    "AdminSearchDomainUsageBucketsInput",
    "AdminSearchProjectUsageBucketsInput",
    "AdminSearchUserUsageBucketsInput",
    "DomainSearchDomainUsageBucketsInput",
    "DomainSearchProjectUsageBucketsInput",
    "DomainSearchUserUsageBucketsInput",
    "DomainUsageBucketFilter",
    "DomainUsageBucketOrderBy",
    "ProjectUsageBucketFilter",
    "ProjectUsageBucketOrderBy",
    "UserUsageBucketFilter",
    "UserUsageBucketOrderBy",
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


# GQL Filter/Order DTOs for usage bucket queries


class DomainUsageBucketFilter(BaseRequestModel):
    """Filter for domain usage bucket queries."""

    resource_group: StringFilter | None = Field(
        default=None, description="Filter by resource group name"
    )
    domain_name: StringFilter | None = Field(default=None, description="Filter by domain name")
    period_start: DateFilter | None = Field(default=None, description="Filter by period start date")
    period_end: DateFilter | None = Field(default=None, description="Filter by period end date")
    AND: list[DomainUsageBucketFilter] | None = Field(
        default=None, description="Combine with AND logic"
    )
    OR: list[DomainUsageBucketFilter] | None = Field(
        default=None, description="Combine with OR logic"
    )
    NOT: list[DomainUsageBucketFilter] | None = Field(default=None, description="Negate filters")


DomainUsageBucketFilter.model_rebuild()


class DomainUsageBucketOrderBy(BaseRequestModel):
    """Ordering specification for domain usage bucket queries."""

    field: UsageBucketOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.DESC, description="Order direction")


class ProjectUsageBucketFilter(BaseRequestModel):
    """Filter for project usage bucket queries."""

    resource_group: StringFilter | None = Field(
        default=None, description="Filter by resource group name"
    )
    project_id: UUIDFilter | None = Field(default=None, description="Filter by project UUID")
    domain_name: StringFilter | None = Field(default=None, description="Filter by domain name")
    period_start: DateFilter | None = Field(default=None, description="Filter by period start date")
    period_end: DateFilter | None = Field(default=None, description="Filter by period end date")
    AND: list[ProjectUsageBucketFilter] | None = Field(
        default=None, description="Combine with AND logic"
    )
    OR: list[ProjectUsageBucketFilter] | None = Field(
        default=None, description="Combine with OR logic"
    )
    NOT: list[ProjectUsageBucketFilter] | None = Field(default=None, description="Negate filters")


ProjectUsageBucketFilter.model_rebuild()


class ProjectUsageBucketOrderBy(BaseRequestModel):
    """Ordering specification for project usage bucket queries."""

    field: UsageBucketOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.DESC, description="Order direction")


class UserUsageBucketFilter(BaseRequestModel):
    """Filter for user usage bucket queries."""

    resource_group: StringFilter | None = Field(
        default=None, description="Filter by resource group name"
    )
    user_uuid: UUIDFilter | None = Field(default=None, description="Filter by user UUID")
    project_id: UUIDFilter | None = Field(default=None, description="Filter by project UUID")
    domain_name: StringFilter | None = Field(default=None, description="Filter by domain name")
    period_start: DateFilter | None = Field(default=None, description="Filter by period start date")
    period_end: DateFilter | None = Field(default=None, description="Filter by period end date")
    AND: list[UserUsageBucketFilter] | None = Field(
        default=None, description="Combine with AND logic"
    )
    OR: list[UserUsageBucketFilter] | None = Field(
        default=None, description="Combine with OR logic"
    )
    NOT: list[UserUsageBucketFilter] | None = Field(default=None, description="Negate filters")


UserUsageBucketFilter.model_rebuild()


class UserUsageBucketOrderBy(BaseRequestModel):
    """Ordering specification for user usage bucket queries."""

    field: UsageBucketOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.DESC, description="Order direction")
