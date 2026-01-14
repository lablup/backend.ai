"""Request DTOs for Fair Share API."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

from .types import (
    DomainFairShareFilter,
    DomainFairShareOrder,
    DomainUsageBucketFilter,
    DomainUsageBucketOrder,
    ProjectFairShareFilter,
    ProjectFairShareOrder,
    ProjectUsageBucketFilter,
    ProjectUsageBucketOrder,
    UserFairShareFilter,
    UserFairShareOrder,
    UserUsageBucketFilter,
    UserUsageBucketOrder,
)

__all__ = (
    # Path parameters
    "GetDomainFairSharePathParam",
    "GetProjectFairSharePathParam",
    "GetUserFairSharePathParam",
    # Get requests (deprecated, use PathParam)
    "GetDomainFairShareRequest",
    "GetProjectFairShareRequest",
    "GetUserFairShareRequest",
    # Search requests
    "SearchDomainFairSharesRequest",
    "SearchProjectFairSharesRequest",
    "SearchUserFairSharesRequest",
    "SearchDomainUsageBucketsRequest",
    "SearchProjectUsageBucketsRequest",
    "SearchUserUsageBucketsRequest",
)


# Path Parameters


class GetDomainFairSharePathParam(BaseRequestModel):
    """Path parameters for getting a single domain fair share."""

    resource_group: str = Field(description="Scaling group name")
    domain_name: str = Field(description="Domain name")


class GetProjectFairSharePathParam(BaseRequestModel):
    """Path parameters for getting a single project fair share."""

    resource_group: str = Field(description="Scaling group name")
    project_id: UUID = Field(description="Project ID")


class GetUserFairSharePathParam(BaseRequestModel):
    """Path parameters for getting a single user fair share."""

    resource_group: str = Field(description="Scaling group name")
    project_id: UUID = Field(description="Project ID")
    user_uuid: UUID = Field(description="User UUID")


# Get Requests (deprecated, use PathParam models above)


class GetDomainFairShareRequest(BaseRequestModel):
    """Request for getting a single domain fair share."""

    resource_group: str = Field(description="Scaling group name")
    domain_name: str = Field(description="Domain name")


class GetProjectFairShareRequest(BaseRequestModel):
    """Request for getting a single project fair share."""

    resource_group: str = Field(description="Scaling group name")
    project_id: UUID = Field(description="Project ID")


class GetUserFairShareRequest(BaseRequestModel):
    """Request for getting a single user fair share."""

    resource_group: str = Field(description="Scaling group name")
    project_id: UUID = Field(description="Project ID")
    user_uuid: UUID = Field(description="User UUID")


# Search Requests


class SearchDomainFairSharesRequest(BaseRequestModel):
    """Request body for searching domain fair shares."""

    filter: Optional[DomainFairShareFilter] = Field(default=None, description="Filter conditions")
    order: Optional[list[DomainFairShareOrder]] = Field(
        default=None, description="Order specifications"
    )
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class SearchProjectFairSharesRequest(BaseRequestModel):
    """Request body for searching project fair shares."""

    filter: Optional[ProjectFairShareFilter] = Field(default=None, description="Filter conditions")
    order: Optional[list[ProjectFairShareOrder]] = Field(
        default=None, description="Order specifications"
    )
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class SearchUserFairSharesRequest(BaseRequestModel):
    """Request body for searching user fair shares."""

    filter: Optional[UserFairShareFilter] = Field(default=None, description="Filter conditions")
    order: Optional[list[UserFairShareOrder]] = Field(
        default=None, description="Order specifications"
    )
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class SearchDomainUsageBucketsRequest(BaseRequestModel):
    """Request body for searching domain usage buckets."""

    filter: Optional[DomainUsageBucketFilter] = Field(default=None, description="Filter conditions")
    order: Optional[list[DomainUsageBucketOrder]] = Field(
        default=None, description="Order specifications"
    )
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class SearchProjectUsageBucketsRequest(BaseRequestModel):
    """Request body for searching project usage buckets."""

    filter: Optional[ProjectUsageBucketFilter] = Field(
        default=None, description="Filter conditions"
    )
    order: Optional[list[ProjectUsageBucketOrder]] = Field(
        default=None, description="Order specifications"
    )
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class SearchUserUsageBucketsRequest(BaseRequestModel):
    """Request body for searching user usage buckets."""

    filter: Optional[UserUsageBucketFilter] = Field(default=None, description="Filter conditions")
    order: Optional[list[UserUsageBucketOrder]] = Field(
        default=None, description="Order specifications"
    )
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")
