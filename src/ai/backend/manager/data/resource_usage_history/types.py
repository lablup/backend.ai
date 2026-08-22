"""Domain data for the usage history tables."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.types import FieldData
from ai.backend.common.types import ResourceSlot


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
    resource_group_id: ResourceGroupID
    period_start: datetime
    period_end: datetime
    resource_usage: ResourceSlot


@dataclass(frozen=True)
class DomainUsageBucketData(FieldData):
    """Domain usage bucket data (period-based aggregation)."""

    id: uuid.UUID
    domain_name: str
    resource_group: str
    resource_group_id: ResourceGroupID
    period_start: date
    period_end: date
    decay_unit_days: int
    resource_usage: ResourceSlot
    capacity_snapshot: ResourceSlot
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ProjectUsageBucketData(FieldData):
    """Project usage bucket data (period-based aggregation)."""

    id: uuid.UUID
    project_id: uuid.UUID
    domain_name: str
    resource_group: str
    resource_group_id: ResourceGroupID
    period_start: date
    period_end: date
    decay_unit_days: int
    resource_usage: ResourceSlot
    capacity_snapshot: ResourceSlot
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class UserUsageBucketData(FieldData):
    """User usage bucket data (period-based aggregation)."""

    id: uuid.UUID
    user_uuid: uuid.UUID
    project_id: uuid.UUID
    domain_name: str
    resource_group: str
    resource_group_id: ResourceGroupID
    period_start: date
    period_end: date
    decay_unit_days: int
    resource_usage: ResourceSlot
    capacity_snapshot: ResourceSlot
    created_at: datetime
    updated_at: datetime
