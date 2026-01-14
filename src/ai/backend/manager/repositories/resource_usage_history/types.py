"""Data classes for Resource Usage History repository layer."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from typing import TYPE_CHECKING

from ai.backend.common.types import ResourceSlot

if TYPE_CHECKING:
    from ai.backend.manager.models.resource_usage_history import (
        DomainUsageBucketRow,
        KernelUsageRecordRow,
        ProjectUsageBucketRow,
        UserUsageBucketRow,
    )


@dataclass(frozen=True)
class KernelUsageRecordData:
    """Kernel usage record data (per-period usage slice)."""

    id: uuid.UUID
    kernel_id: uuid.UUID
    session_id: uuid.UUID
    user_uuid: uuid.UUID
    project_id: uuid.UUID
    domain_name: str
    resource_group: str
    period_start: datetime
    period_end: datetime
    resource_usage: ResourceSlot

    @classmethod
    def from_row(cls, row: KernelUsageRecordRow) -> KernelUsageRecordData:
        """Create KernelUsageRecordData from a KernelUsageRecordRow."""
        return cls(
            id=row.id,
            kernel_id=row.kernel_id,
            session_id=row.session_id,
            user_uuid=row.user_uuid,
            project_id=row.project_id,
            domain_name=row.domain_name,
            resource_group=row.resource_group,
            period_start=row.period_start,
            period_end=row.period_end,
            resource_usage=row.resource_usage,
        )


@dataclass(frozen=True)
class DomainUsageBucketData:
    """Domain usage bucket data (period-based aggregation)."""

    id: uuid.UUID
    domain_name: str
    resource_group: str
    period_start: date
    period_end: date
    decay_unit_days: int
    resource_usage: ResourceSlot
    capacity_snapshot: ResourceSlot
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row: DomainUsageBucketRow) -> DomainUsageBucketData:
        """Create DomainUsageBucketData from a DomainUsageBucketRow."""
        return cls(
            id=row.id,
            domain_name=row.domain_name,
            resource_group=row.resource_group,
            period_start=row.period_start,
            period_end=row.period_end,
            decay_unit_days=row.decay_unit_days,
            resource_usage=row.resource_usage,
            capacity_snapshot=row.capacity_snapshot,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


@dataclass(frozen=True)
class ProjectUsageBucketData:
    """Project usage bucket data (period-based aggregation)."""

    id: uuid.UUID
    project_id: uuid.UUID
    domain_name: str
    resource_group: str
    period_start: date
    period_end: date
    decay_unit_days: int
    resource_usage: ResourceSlot
    capacity_snapshot: ResourceSlot
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row: ProjectUsageBucketRow) -> ProjectUsageBucketData:
        """Create ProjectUsageBucketData from a ProjectUsageBucketRow."""
        return cls(
            id=row.id,
            project_id=row.project_id,
            domain_name=row.domain_name,
            resource_group=row.resource_group,
            period_start=row.period_start,
            period_end=row.period_end,
            decay_unit_days=row.decay_unit_days,
            resource_usage=row.resource_usage,
            capacity_snapshot=row.capacity_snapshot,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


@dataclass(frozen=True)
class UserUsageBucketData:
    """User usage bucket data (period-based aggregation)."""

    id: uuid.UUID
    user_uuid: uuid.UUID
    project_id: uuid.UUID
    domain_name: str
    resource_group: str
    period_start: date
    period_end: date
    decay_unit_days: int
    resource_usage: ResourceSlot
    capacity_snapshot: ResourceSlot
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row: UserUsageBucketRow) -> UserUsageBucketData:
        """Create UserUsageBucketData from a UserUsageBucketRow."""
        return cls(
            id=row.id,
            user_uuid=row.user_uuid,
            project_id=row.project_id,
            domain_name=row.domain_name,
            resource_group=row.resource_group,
            period_start=row.period_start,
            period_end=row.period_end,
            decay_unit_days=row.decay_unit_days,
            resource_usage=row.resource_usage,
            capacity_snapshot=row.capacity_snapshot,
            created_at=row.created_at,
            updated_at=row.updated_at,
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
