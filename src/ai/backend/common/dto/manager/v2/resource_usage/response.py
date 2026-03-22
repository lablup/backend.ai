"""Response DTOs for Resource Usage DTO v2."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.fair_share.types import ResourceSlotInfo

__all__ = (
    "UsageBucketMetadataNode",
    "DomainUsageBucketNode",
    "ProjectUsageBucketNode",
    "UserUsageBucketNode",
    "AdminSearchDomainUsageBucketsPayload",
    "AdminSearchProjectUsageBucketsPayload",
    "AdminSearchUserUsageBucketsPayload",
    "DomainSearchDomainUsageBucketsPayload",
    "DomainSearchProjectUsageBucketsPayload",
    "DomainSearchUserUsageBucketsPayload",
)


class UsageBucketMetadataNode(BaseResponseModel):
    """Common metadata for usage bucket records."""

    period_start: date = Field(
        description="Start date of the usage measurement period (inclusive)."
    )
    period_end: date = Field(description="End date of the usage measurement period (exclusive).")
    decay_unit_days: int = Field(description="Number of days in each decay unit for this bucket.")
    created_at: datetime = Field(description="Timestamp when this record was created.")
    updated_at: datetime = Field(description="Timestamp when this record was last updated.")


class DomainUsageBucketNode(BaseResponseModel):
    """Node model representing a domain usage bucket."""

    id: UUID = Field(description="Usage bucket ID")
    domain_name: str = Field(description="Domain name")
    resource_group_name: str = Field(description="Resource group name")
    metadata: UsageBucketMetadataNode = Field(description="Usage measurement period metadata")
    resource_usage: ResourceSlotInfo = Field(description="Resource usage snapshot")
    capacity_snapshot: ResourceSlotInfo = Field(description="Capacity snapshot at period end")


class ProjectUsageBucketNode(BaseResponseModel):
    """Node model representing a project usage bucket."""

    id: UUID = Field(description="Usage bucket ID")
    project_id: UUID = Field(description="Project ID")
    domain_name: str = Field(description="Domain name")
    resource_group_name: str = Field(description="Resource group name")
    metadata: UsageBucketMetadataNode = Field(description="Usage measurement period metadata")
    resource_usage: ResourceSlotInfo = Field(description="Resource usage snapshot")
    capacity_snapshot: ResourceSlotInfo = Field(description="Capacity snapshot at period end")


class UserUsageBucketNode(BaseResponseModel):
    """Node model representing a user usage bucket."""

    id: UUID = Field(description="Usage bucket ID")
    user_uuid: UUID = Field(description="User UUID")
    project_id: UUID = Field(description="Project ID")
    domain_name: str = Field(description="Domain name")
    resource_group_name: str = Field(description="Resource group name")
    metadata: UsageBucketMetadataNode = Field(description="Usage measurement period metadata")
    resource_usage: ResourceSlotInfo = Field(description="Resource usage snapshot")
    capacity_snapshot: ResourceSlotInfo = Field(description="Capacity snapshot at period end")


class AdminSearchDomainUsageBucketsPayload(BaseResponseModel):
    """Payload for admin domain usage bucket search result."""

    items: list[DomainUsageBucketNode] = Field(description="Domain usage bucket list")
    total_count: int = Field(description="Total count")
    has_next_page: bool = Field(description="Whether a next page exists")
    has_previous_page: bool = Field(description="Whether a previous page exists")


class AdminSearchProjectUsageBucketsPayload(BaseResponseModel):
    """Payload for admin project usage bucket search result."""

    items: list[ProjectUsageBucketNode] = Field(description="Project usage bucket list")
    total_count: int = Field(description="Total count")
    has_next_page: bool = Field(description="Whether a next page exists")
    has_previous_page: bool = Field(description="Whether a previous page exists")


class AdminSearchUserUsageBucketsPayload(BaseResponseModel):
    """Payload for admin user usage bucket search result."""

    items: list[UserUsageBucketNode] = Field(description="User usage bucket list")
    total_count: int = Field(description="Total count")
    has_next_page: bool = Field(description="Whether a next page exists")
    has_previous_page: bool = Field(description="Whether a previous page exists")


class DomainSearchDomainUsageBucketsPayload(BaseResponseModel):
    """Payload for scoped domain usage bucket search result."""

    items: list[DomainUsageBucketNode] = Field(description="Domain usage bucket list")
    total_count: int = Field(description="Total count")
    has_next_page: bool = Field(description="Whether a next page exists")
    has_previous_page: bool = Field(description="Whether a previous page exists")


class DomainSearchProjectUsageBucketsPayload(BaseResponseModel):
    """Payload for scoped project usage bucket search result."""

    items: list[ProjectUsageBucketNode] = Field(description="Project usage bucket list")
    total_count: int = Field(description="Total count")
    has_next_page: bool = Field(description="Whether a next page exists")
    has_previous_page: bool = Field(description="Whether a previous page exists")


class DomainSearchUserUsageBucketsPayload(BaseResponseModel):
    """Payload for scoped user usage bucket search result."""

    items: list[UserUsageBucketNode] = Field(description="User usage bucket list")
    total_count: int = Field(description="Total count")
    has_next_page: bool = Field(description="Whether a next page exists")
    has_previous_page: bool = Field(description="Whether a previous page exists")
