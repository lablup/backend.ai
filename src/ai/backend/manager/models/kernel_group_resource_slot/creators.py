"""Insert specs for the kernel_group_resource_slots table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import override

from ai.backend.common.data.entity.kernel_group import KernelGroupID
from ai.backend.common.data.entity.kernel_group_resource_slot import KernelGroupResourceSlotID
from ai.backend.common.data.entity.resource_slot import ResourceSlotName
from ai.backend.manager.data.kernel_group.types import KernelGroupResourceSlotData
from ai.backend.manager.models.kernel_group_resource_slot.row import KernelGroupResourceSlotRow
from ai.backend.manager.models.specs.creator import NestedFieldCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck

__all__ = ("KernelGroupResourceSlotCreator",)


@dataclass(frozen=True)
class KernelGroupResourceSlotCreator(
    NestedFieldCreator[KernelGroupID, KernelGroupResourceSlotRow, KernelGroupResourceSlotData]
):
    """Record what one kernel group asked for in one slot."""

    slot_name: ResourceSlotName
    quantity: Decimal

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self, owner_id: KernelGroupID) -> KernelGroupResourceSlotRow:
        return KernelGroupResourceSlotRow(
            kernel_group_id=owner_id,
            slot_name=self.slot_name,
            quantity=self.quantity,
        )

    @override
    def to_data(self, row: KernelGroupResourceSlotRow) -> KernelGroupResourceSlotData:
        return KernelGroupResourceSlotData(
            id=KernelGroupResourceSlotID(row.id),
            kernel_group_id=row.kernel_group_id,
            slot_name=ResourceSlotName(row.slot_name),
            quantity=row.quantity,
        )
