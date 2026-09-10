"""Insert specs for the kernel_usage_records table."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import override

from ai.backend.common.data.entity.kernel import KernelID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.resource_usage_history.types import KernelUsageRecordData
from ai.backend.manager.models.resource_usage_history.row import KernelUsageRecordRow
from ai.backend.manager.models.specs.creator import NestedFieldCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class KernelUsageRecordCreator(
    NestedFieldCreator[KernelID, KernelUsageRecordRow, KernelUsageRecordData]
):
    """One period slice of a kernel's resource usage, owned by the kernel it observed.

    A kernel is itself a field of its session, so a slice under it is nested: what
    answers for the slice is what answers for the kernel.
    """

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
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self, owner_id: KernelID) -> KernelUsageRecordRow:
        return KernelUsageRecordRow(
            kernel_id=owner_id,
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

    @override
    def to_data(self, row: KernelUsageRecordRow) -> KernelUsageRecordData:
        return row.to_data()
