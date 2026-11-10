from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.kernel_scheduling_history import KernelSchedulingHistoryID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.manager.actions.v2.field.ops import PartialBulkGetFieldOpsAction
from ai.backend.manager.data.kernel.types import KernelSchedulingHistoryData
from ai.backend.manager.models.scheduling_history.queriers import (
    BulkKernelSchedulingHistoryQuerier,
)
from ai.backend.manager.models.scheduling_history.row import KernelSchedulingHistoryRow
from ai.backend.manager.services.scheduling_history.actions.lookup_owner import (
    LookupBulkKernelSchedulingHistoryOwnerAction,
)


@dataclass
class BulkGetKernelHistoriesAction(
    PartialBulkGetFieldOpsAction[
        KernelSchedulingHistoryID,
        SessionID,
        KernelSchedulingHistoryRow,
        KernelSchedulingHistoryData,
    ]
):
    """Read the kernel scheduling history rows the caller named."""

    ids: Sequence[KernelSchedulingHistoryID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_kernel_histories"

    @override
    def field_ids(self) -> Sequence[KernelSchedulingHistoryID]:
        return tuple(self.ids)

    @override
    def to_owner_lookup_action(self) -> LookupBulkKernelSchedulingHistoryOwnerAction:
        return LookupBulkKernelSchedulingHistoryOwnerAction(history_ids=self.ids)

    @override
    def to_querier(self) -> BulkKernelSchedulingHistoryQuerier:
        return BulkKernelSchedulingHistoryQuerier()

    @override
    def narrowed_to(self, field_ids: Sequence[KernelSchedulingHistoryID]) -> Self:
        allowed = frozenset(field_ids)
        return replace(self, ids=[field_id for field_id in self.ids if field_id in allowed])
