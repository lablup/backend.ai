"""Upserter specs for Resource Usage History repository upsert operations."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from typing import Any, override

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.models.resource_usage_history import (
    DomainUsageBucketRow,
    ProjectUsageBucketRow,
    UserUsageBucketRow,
)
from ai.backend.manager.repositories.base import UpserterSpec


@dataclass
class DomainUsageBucketUpserterSpec(UpserterSpec[DomainUsageBucketRow]):
    """Upserter spec for DomainUsageBucketRow.

    Unique constraint: (domain_name, resource_group, period_start)
    """

    domain_name: str
    resource_group: str
    period_start: date
    period_end: date
    decay_unit_days: int = 1
    resource_usage: ResourceSlot | None = None
    capacity_snapshot: ResourceSlot | None = None

    @property
    @override
    def row_class(self) -> type[DomainUsageBucketRow]:
        return DomainUsageBucketRow

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {
            "domain_name": self.domain_name,
            "resource_group": self.resource_group,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "decay_unit_days": self.decay_unit_days,
            "resource_usage": self.resource_usage or ResourceSlot(),
            "capacity_snapshot": self.capacity_snapshot or ResourceSlot(),
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {"period_end": self.period_end}
        if self.resource_usage is not None:
            values["resource_usage"] = self.resource_usage
        if self.capacity_snapshot is not None:
            values["capacity_snapshot"] = self.capacity_snapshot
        return values


@dataclass
class ProjectUsageBucketUpserterSpec(UpserterSpec[ProjectUsageBucketRow]):
    """Upserter spec for ProjectUsageBucketRow.

    Unique constraint: (project_id, resource_group, period_start)
    """

    project_id: uuid.UUID
    domain_name: str
    resource_group: str
    period_start: date
    period_end: date
    decay_unit_days: int = 1
    resource_usage: ResourceSlot | None = None
    capacity_snapshot: ResourceSlot | None = None

    @property
    @override
    def row_class(self) -> type[ProjectUsageBucketRow]:
        return ProjectUsageBucketRow

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "domain_name": self.domain_name,
            "resource_group": self.resource_group,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "decay_unit_days": self.decay_unit_days,
            "resource_usage": self.resource_usage or ResourceSlot(),
            "capacity_snapshot": self.capacity_snapshot or ResourceSlot(),
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {"period_end": self.period_end}
        if self.resource_usage is not None:
            values["resource_usage"] = self.resource_usage
        if self.capacity_snapshot is not None:
            values["capacity_snapshot"] = self.capacity_snapshot
        return values


@dataclass
class UserUsageBucketUpserterSpec(UpserterSpec[UserUsageBucketRow]):
    """Upserter spec for UserUsageBucketRow.

    Unique constraint: (user_uuid, project_id, resource_group, period_start)
    """

    user_uuid: uuid.UUID
    project_id: uuid.UUID
    domain_name: str
    resource_group: str
    period_start: date
    period_end: date
    decay_unit_days: int = 1
    resource_usage: ResourceSlot | None = None
    capacity_snapshot: ResourceSlot | None = None

    @property
    @override
    def row_class(self) -> type[UserUsageBucketRow]:
        return UserUsageBucketRow

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {
            "user_uuid": self.user_uuid,
            "project_id": self.project_id,
            "domain_name": self.domain_name,
            "resource_group": self.resource_group,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "decay_unit_days": self.decay_unit_days,
            "resource_usage": self.resource_usage or ResourceSlot(),
            "capacity_snapshot": self.capacity_snapshot or ResourceSlot(),
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {"period_end": self.period_end}
        if self.resource_usage is not None:
            values["resource_usage"] = self.resource_usage
        if self.capacity_snapshot is not None:
            values["capacity_snapshot"] = self.capacity_snapshot
        return values
