"""Data classes for Resource Usage History repository layer."""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.manager.data.resource_usage_history.types import (
    DomainUsageBucketData,
    KernelUsageRecordData,
    ProjectUsageBucketData,
    UserUsageBucketData,
)


@dataclass(frozen=True)
class KernelUsageRecordSearchResult:
    """Search result with pagination info for kernel usage records."""

    items: list[KernelUsageRecordData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass(frozen=True)
class DomainUsageBucketSearchResult:
    """Search result with pagination info for domain usage buckets."""

    items: list[DomainUsageBucketData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass(frozen=True)
class ProjectUsageBucketSearchResult:
    """Search result with pagination info for project usage buckets."""

    items: list[ProjectUsageBucketData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass(frozen=True)
class UserUsageBucketSearchResult:
    """Search result with pagination info for user usage buckets."""

    items: list[UserUsageBucketData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
