from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.kernel_group_resource_slot import KernelGroupResourceSlotID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.manager.actions.v2.field.ops import PartialBulkGetFieldOpsAction
from ai.backend.manager.data.kernel_group.types import KernelGroupResourceSlotData
from ai.backend.manager.models.kernel_group_resource_slot.queriers import (
    BulkKernelGroupResourceSlotQuerier,
)
from ai.backend.manager.models.kernel_group_resource_slot.row import KernelGroupResourceSlotRow
from ai.backend.manager.services.session.actions.lookup_bulk_kernel_group_resource_slot_owner import (
    LookupBulkKernelGroupResourceSlotOwnerAction,
)


@dataclass(frozen=True)
class BulkGetKernelGroupResourceSlotsAction(
    PartialBulkGetFieldOpsAction[
        KernelGroupResourceSlotID,
        SessionID,
        KernelGroupResourceSlotRow,
        KernelGroupResourceSlotData,
    ]
):
    """Read the kernel group resource slot rows the caller named, answering for each one."""

    ids: Sequence[KernelGroupResourceSlotID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_kernel_group_resource_slots"

    @override
    def field_ids(self) -> Sequence[KernelGroupResourceSlotID]:
        return tuple(self.ids)

    @override
    def to_owner_lookup_action(self) -> LookupBulkKernelGroupResourceSlotOwnerAction:
        return LookupBulkKernelGroupResourceSlotOwnerAction(kernel_group_resource_slot_ids=self.ids)

    @override
    def to_querier(self) -> BulkKernelGroupResourceSlotQuerier:
        return BulkKernelGroupResourceSlotQuerier()

    @override
    def narrowed_to(self, field_ids: Sequence[KernelGroupResourceSlotID]) -> Self:
        allowed = frozenset(field_ids)
        return replace(self, ids=[field_id for field_id in self.ids if field_id in allowed])
