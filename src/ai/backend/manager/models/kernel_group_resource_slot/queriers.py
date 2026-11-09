from __future__ import annotations

from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.manager.data.kernel_group.types import KernelGroupResourceSlotData
from ai.backend.manager.models.kernel_group_resource_slot.row import KernelGroupResourceSlotRow
from ai.backend.manager.models.specs.querier import BulkFieldQuerier


class BulkKernelGroupResourceSlotQuerier(
    BulkFieldQuerier[KernelGroupResourceSlotRow, KernelGroupResourceSlotData]
):
    """The resource slot rows the caller named."""

    @override
    def row_class(self) -> type[KernelGroupResourceSlotRow]:
        return KernelGroupResourceSlotRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return KernelGroupResourceSlotRow.id

    @override
    def to_data(self, row: KernelGroupResourceSlotRow) -> KernelGroupResourceSlotData:
        return row.to_data()
