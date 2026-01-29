"""Type definitions for Fair Share DTOs."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter

__all__ = (
    # Enums
    "OrderDirection",
    # Domain Fair Share
    "DomainFairShareOrderField",
    "DomainFairShareFilter",
    "DomainFairShareOrder",
    # Project Fair Share
    "ProjectFairShareOrderField",
    "ProjectFairShareFilter",
    "ProjectFairShareOrder",
    # User Fair Share
    "UserFairShareOrderField",
    "UserFairShareFilter",
    "UserFairShareOrder",
    # Domain Usage Bucket
    "DomainUsageBucketOrderField",
    "DomainUsageBucketFilter",
    "DomainUsageBucketOrder",
    # Project Usage Bucket
    "ProjectUsageBucketOrderField",
    "ProjectUsageBucketFilter",
    "ProjectUsageBucketOrder",
    # User Usage Bucket
    "UserUsageBucketOrderField",
    "UserUsageBucketFilter",
    "UserUsageBucketOrder",
)


class OrderDirection(StrEnum):
    ASC = "asc"
    DESC = "desc"


# Domain Fair Share


class DomainFairShareOrderField(StrEnum):
    FAIR_SHARE_FACTOR = "fair_share_factor"
    DOMAIN_NAME = "domain_name"
    CREATED_AT = "created_at"


class DomainFairShareFilter(BaseRequestModel):
    """Filter for domain fair share queries."""

    resource_group: StringFilter | None = Field(default=None, description="Filter by scaling group")
    domain_name: StringFilter | None = Field(default=None, description="Filter by domain name")


class DomainFairShareOrder(BaseRequestModel):
    """Order specification for domain fair share queries."""

    field: DomainFairShareOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.DESC, description="Order direction")


# Project Fair Share


class ProjectFairShareOrderField(StrEnum):
    FAIR_SHARE_FACTOR = "fair_share_factor"
    CREATED_AT = "created_at"


class ProjectFairShareFilter(BaseRequestModel):
    """Filter for project fair share queries."""

    resource_group: StringFilter | None = Field(default=None, description="Filter by scaling group")
    project_id: UUIDFilter | None = Field(default=None, description="Filter by project ID")
    domain_name: StringFilter | None = Field(default=None, description="Filter by domain name")


class ProjectFairShareOrder(BaseRequestModel):
    """Order specification for project fair share queries."""

    field: ProjectFairShareOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.DESC, description="Order direction")


# User Fair Share


class UserFairShareOrderField(StrEnum):
    FAIR_SHARE_FACTOR = "fair_share_factor"
    CREATED_AT = "created_at"


class UserFairShareFilter(BaseRequestModel):
    """Filter for user fair share queries."""

    resource_group: StringFilter | None = Field(default=None, description="Filter by scaling group")
    user_uuid: UUIDFilter | None = Field(default=None, description="Filter by user UUID")
    project_id: UUIDFilter | None = Field(default=None, description="Filter by project ID")
    domain_name: StringFilter | None = Field(default=None, description="Filter by domain name")


class UserFairShareOrder(BaseRequestModel):
    """Order specification for user fair share queries."""

    field: UserFairShareOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.DESC, description="Order direction")


# Domain Usage Bucket


class DomainUsageBucketOrderField(StrEnum):
    PERIOD_START = "period_start"


class DomainUsageBucketFilter(BaseRequestModel):
    """Filter for domain usage bucket queries."""

    resource_group: StringFilter | None = Field(default=None, description="Filter by scaling group")
    domain_name: StringFilter | None = Field(default=None, description="Filter by domain name")


class DomainUsageBucketOrder(BaseRequestModel):
    """Order specification for domain usage bucket queries."""

    field: DomainUsageBucketOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.DESC, description="Order direction")


# Project Usage Bucket


class ProjectUsageBucketOrderField(StrEnum):
    PERIOD_START = "period_start"


class ProjectUsageBucketFilter(BaseRequestModel):
    """Filter for project usage bucket queries."""

    resource_group: StringFilter | None = Field(default=None, description="Filter by scaling group")
    project_id: UUIDFilter | None = Field(default=None, description="Filter by project ID")
    domain_name: StringFilter | None = Field(default=None, description="Filter by domain name")


class ProjectUsageBucketOrder(BaseRequestModel):
    """Order specification for project usage bucket queries."""

    field: ProjectUsageBucketOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.DESC, description="Order direction")


# User Usage Bucket


class UserUsageBucketOrderField(StrEnum):
    PERIOD_START = "period_start"


class UserUsageBucketFilter(BaseRequestModel):
    """Filter for user usage bucket queries."""

    resource_group: StringFilter | None = Field(default=None, description="Filter by scaling group")
    user_uuid: UUIDFilter | None = Field(default=None, description="Filter by user UUID")
    project_id: UUIDFilter | None = Field(default=None, description="Filter by project ID")
    domain_name: StringFilter | None = Field(default=None, description="Filter by domain name")


class UserUsageBucketOrder(BaseRequestModel):
    """Order specification for user usage bucket queries."""

    field: UserUsageBucketOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.DESC, description="Order direction")
