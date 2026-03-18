"""Response DTOs for Resource Usage DTO v2."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
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


class DomainUsageBucketNode(BaseResponseModel):
    """Node model representing a domain usage bucket."""

    id: UUID = Field(description="Usage bucket ID")
    domain_name: str = Field(description="Domain name")
    resource_group: str = Field(description="Resource group name")
    period_start: date = Field(description="Period start date")
    period_end: date = Field(description="Period end date")
    decay_unit_days: int = Field(description="Decay unit in days")
    resource_usage: dict[str, Any] = Field(description="Resource usage snapshot")
    capacity_snapshot: dict[str, Any] = Field(description="Capacity snapshot at period start")
    created_at: datetime = Field(description="Record creation timestamp")
    updated_at: datetime = Field(description="Record last update timestamp")


class ProjectUsageBucketNode(BaseResponseModel):
    """Node model representing a project usage bucket."""

    id: UUID = Field(description="Usage bucket ID")
    project_id: UUID = Field(description="Project ID")
    domain_name: str = Field(description="Domain name")
    resource_group: str = Field(description="Resource group name")
    period_start: date = Field(description="Period start date")
    period_end: date = Field(description="Period end date")
    decay_unit_days: int = Field(description="Decay unit in days")
    resource_usage: dict[str, Any] = Field(description="Resource usage snapshot")
    capacity_snapshot: dict[str, Any] = Field(description="Capacity snapshot at period start")
    created_at: datetime = Field(description="Record creation timestamp")
    updated_at: datetime = Field(description="Record last update timestamp")


class UserUsageBucketNode(BaseResponseModel):
    """Node model representing a user usage bucket."""

    id: UUID = Field(description="Usage bucket ID")
    user_uuid: UUID = Field(description="User UUID")
    project_id: UUID = Field(description="Project ID")
    domain_name: str = Field(description="Domain name")
    resource_group: str = Field(description="Resource group name")
    period_start: date = Field(description="Period start date")
    period_end: date = Field(description="Period end date")
    decay_unit_days: int = Field(description="Decay unit in days")
    resource_usage: dict[str, Any] = Field(description="Resource usage snapshot")
    capacity_snapshot: dict[str, Any] = Field(description="Capacity snapshot at period start")
    created_at: datetime = Field(description="Record creation timestamp")
    updated_at: datetime = Field(description="Record last update timestamp")


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
