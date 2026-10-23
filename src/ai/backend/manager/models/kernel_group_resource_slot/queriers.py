from __future__ import annotations

from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.manager.data.kernel_group.types import KernelGroupResourceSlotData
from ai.backend.manager.models.kernel_group_resource_slot.row import KernelGroupResourceSlotRow
from ai.backend.manager.models.specs.querier import BulkNestedFieldQuerier


class BulkKernelGroupResourceSlotQuerier(
    BulkNestedFieldQuerier[KernelGroupResourceSlotRow, KernelGroupResourceSlotData]
):
    """The resource slot rows of the kernel groups the caller named, in slot name order."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(KernelGroupResourceSlotRow).order_by(KernelGroupResourceSlotRow.slot_name)

    @override
    def parent_id_column(self) -> InstrumentedAttribute[Any]:
        return KernelGroupResourceSlotRow.kernel_group_id

    @override
    def to_data(self, row: KernelGroupResourceSlotRow) -> KernelGroupResourceSlotData:
        return row.to_data()
