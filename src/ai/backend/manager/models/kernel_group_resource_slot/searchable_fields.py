"""What a kernel group resource slot search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.manager.data.kernel_group.types import KernelGroupResourceSlotData
from ai.backend.manager.models.kernel_group_resource_slot.row import KernelGroupResourceSlotRow
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField


class _KernelGroupResourceSlotOwnFields(
    RowDataConverter[KernelGroupResourceSlotRow, KernelGroupResourceSlotData]
):
    """The resource slot row's own columns."""

    field_id = SearchableField(
        KernelGroupResourceSlotRow.id,
        UUIDConditions(KernelGroupResourceSlotRow.id),
        ColumnOrder(KernelGroupResourceSlotRow.id),
    )
    kernel_group_id = SearchableField(
        KernelGroupResourceSlotRow.kernel_group_id,
        UUIDConditions(KernelGroupResourceSlotRow.kernel_group_id),
        ColumnOrder(KernelGroupResourceSlotRow.kernel_group_id),
    )
    slot_name = SearchableField(
        KernelGroupResourceSlotRow.slot_name,
        StringConditions(KernelGroupResourceSlotRow.slot_name),
        ColumnOrder(KernelGroupResourceSlotRow.slot_name),
    )

    @override
    def to_data(self, row: KernelGroupResourceSlotRow) -> KernelGroupResourceSlotData:
        return row.to_data()


class KernelGroupResourceSlotSearchableFields:
    own = _KernelGroupResourceSlotOwnFields()
