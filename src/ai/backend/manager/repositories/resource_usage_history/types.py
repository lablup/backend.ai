"""Data classes for Resource Usage History repository layer."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import sqlalchemy as sa

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.errors.resource import DomainNotFound, ProjectNotFound, ScalingGroupNotFound
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.resource_usage_history import (
    DomainUsageBucketRow,
    KernelUsageRecordRow,
    ProjectUsageBucketRow,
    UserUsageBucketRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.base import ExistenceCheck, QueryCondition, SearchScope


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


# SearchScope classes for scoped usage bucket APIs


@dataclass(frozen=True)
class DomainUsageBucketSearchScope(SearchScope):
    """Scope for domain usage bucket queries."""

    resource_group: str
    domain_name: str

    def to_condition(self) -> QueryCondition:
        resource_group = self.resource_group
        domain_name = self.domain_name

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                DomainUsageBucketRow.resource_group == resource_group,
                DomainUsageBucketRow.domain_name == domain_name,
            )

        return inner

    @property
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return [
            ExistenceCheck(
                column=ScalingGroupRow.name,
                value=self.resource_group,
                error=ScalingGroupNotFound(self.resource_group),
            ),
            ExistenceCheck(
                column=DomainRow.name,
                value=self.domain_name,
                error=DomainNotFound(self.domain_name),
            ),
        ]


@dataclass(frozen=True)
class ProjectUsageBucketSearchScope(SearchScope):
    """Scope for project usage bucket queries."""

    resource_group: str
    domain_name: str
    project_id: uuid.UUID

    def to_condition(self) -> QueryCondition:
        resource_group = self.resource_group
        domain_name = self.domain_name
        project_id = self.project_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                ProjectUsageBucketRow.resource_group == resource_group,
                ProjectUsageBucketRow.domain_name == domain_name,
                ProjectUsageBucketRow.project_id == project_id,
            )

        return inner

    @property
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return [
            ExistenceCheck(
                column=ScalingGroupRow.name,
                value=self.resource_group,
                error=ScalingGroupNotFound(self.resource_group),
            ),
            ExistenceCheck(
                column=DomainRow.name,
                value=self.domain_name,
                error=DomainNotFound(self.domain_name),
            ),
            ExistenceCheck(
                column=GroupRow.id,
                value=self.project_id,
                error=ProjectNotFound(extra_data={"project_id": str(self.project_id)}),
            ),
        ]


@dataclass(frozen=True)
class UserUsageBucketSearchScope(SearchScope):
    """Scope for user usage bucket queries."""

    resource_group: str
    domain_name: str
    project_id: uuid.UUID
    user_uuid: uuid.UUID

    def to_condition(self) -> QueryCondition:
        resource_group = self.resource_group
        domain_name = self.domain_name
        project_id = self.project_id
        user_uuid = self.user_uuid

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                UserUsageBucketRow.resource_group == resource_group,
                UserUsageBucketRow.domain_name == domain_name,
                UserUsageBucketRow.project_id == project_id,
                UserUsageBucketRow.user_uuid == user_uuid,
            )

        return inner

    @property
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return [
            ExistenceCheck(
                column=ScalingGroupRow.name,
                value=self.resource_group,
                error=ScalingGroupNotFound(self.resource_group),
            ),
            ExistenceCheck(
                column=DomainRow.name,
                value=self.domain_name,
                error=DomainNotFound(self.domain_name),
            ),
            ExistenceCheck(
                column=GroupRow.id,
                value=self.project_id,
                error=ProjectNotFound(extra_data={"project_id": str(self.project_id)}),
            ),
            ExistenceCheck(
                column=UserRow.uuid,
                value=self.user_uuid,
                error=UserNotFound(extra_data={"user_uuid": str(self.user_uuid)}),
            ),
        ]
