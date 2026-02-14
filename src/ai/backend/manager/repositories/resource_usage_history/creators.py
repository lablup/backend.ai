"""Creator specs for Resource Usage History repository INSERT operations."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from typing import override

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.models.resource_usage_history import (
    DomainUsageBucketRow,
    KernelUsageRecordRow,
    ProjectUsageBucketRow,
    UserUsageBucketRow,
)
from ai.backend.manager.repositories.base import CreatorSpec


@dataclass
class KernelUsageRecordCreatorSpec(CreatorSpec[KernelUsageRecordRow]):
    """Creator spec for KernelUsageRecordRow.

    Used for recording per-period kernel resource usage slices.
    """

    kernel_id: uuid.UUID
    session_id: uuid.UUID
    user_uuid: uuid.UUID
    project_id: uuid.UUID
    domain_name: str
    resource_group: str
    period_start: datetime
    period_end: datetime
    resource_usage: ResourceSlot
    # Raw occupied_slots (not pre-multiplied) used by bucket entry normalization.
    # Not persisted to the kernel_usage_records table.
    occupied_slots: ResourceSlot | None = None

    @override
    def build_row(self) -> KernelUsageRecordRow:
        return KernelUsageRecordRow(
            kernel_id=self.kernel_id,
            session_id=self.session_id,
            user_uuid=self.user_uuid,
            project_id=self.project_id,
            domain_name=self.domain_name,
            resource_group=self.resource_group,
            period_start=self.period_start,
            period_end=self.period_end,
            resource_usage=self.resource_usage,
        )


@dataclass
class DomainUsageBucketCreatorSpec(CreatorSpec[DomainUsageBucketRow]):
    """Creator spec for DomainUsageBucketRow."""

    domain_name: str
    resource_group: str
    period_start: date
    period_end: date
    decay_unit_days: int = 1
    resource_usage: ResourceSlot | None = None
    capacity_snapshot: ResourceSlot | None = None

    @override
    def build_row(self) -> DomainUsageBucketRow:
        return DomainUsageBucketRow(
            domain_name=self.domain_name,
            resource_group=self.resource_group,
            period_start=self.period_start,
            period_end=self.period_end,
            decay_unit_days=self.decay_unit_days,
            resource_usage=self.resource_usage or ResourceSlot(),
            capacity_snapshot=self.capacity_snapshot or ResourceSlot(),
        )


@dataclass
class ProjectUsageBucketCreatorSpec(CreatorSpec[ProjectUsageBucketRow]):
    """Creator spec for ProjectUsageBucketRow."""

    project_id: uuid.UUID
    domain_name: str
    resource_group: str
    period_start: date
    period_end: date
    decay_unit_days: int = 1
    resource_usage: ResourceSlot | None = None
    capacity_snapshot: ResourceSlot | None = None

    @override
    def build_row(self) -> ProjectUsageBucketRow:
        return ProjectUsageBucketRow(
            project_id=self.project_id,
            domain_name=self.domain_name,
            resource_group=self.resource_group,
            period_start=self.period_start,
            period_end=self.period_end,
            decay_unit_days=self.decay_unit_days,
            resource_usage=self.resource_usage or ResourceSlot(),
            capacity_snapshot=self.capacity_snapshot or ResourceSlot(),
        )


@dataclass
class UserUsageBucketCreatorSpec(CreatorSpec[UserUsageBucketRow]):
    """Creator spec for UserUsageBucketRow."""

    user_uuid: uuid.UUID
    project_id: uuid.UUID
    domain_name: str
    resource_group: str
    period_start: date
    period_end: date
    decay_unit_days: int = 1
    resource_usage: ResourceSlot | None = None
    capacity_snapshot: ResourceSlot | None = None

    @override
    def build_row(self) -> UserUsageBucketRow:
        return UserUsageBucketRow(
            user_uuid=self.user_uuid,
            project_id=self.project_id,
            domain_name=self.domain_name,
            resource_group=self.resource_group,
            period_start=self.period_start,
            period_end=self.period_end,
            decay_unit_days=self.decay_unit_days,
            resource_usage=self.resource_usage or ResourceSlot(),
            capacity_snapshot=self.capacity_snapshot or ResourceSlot(),
        )
