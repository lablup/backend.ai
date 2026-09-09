"""Creator specs for Resource Usage History repository INSERT operations."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import override

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.models.resource_usage_history import KernelUsageRecordRow
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
    resource_group_id: ResourceGroupID
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
            resource_group_id=self.resource_group_id,
            period_start=self.period_start,
            period_end=self.period_end,
            resource_usage=self.resource_usage,
        )
