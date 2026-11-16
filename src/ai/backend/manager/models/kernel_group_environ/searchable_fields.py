"""What a kernel group environ search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.manager.data.kernel_group.types import KernelGroupEnvironData
from ai.backend.manager.models.kernel_group_environ.row import KernelGroupEnvironRow
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField


class _KernelGroupEnvironOwnFields(RowDataConverter[KernelGroupEnvironRow, KernelGroupEnvironData]):
    """The environ row's own columns."""

    field_id = SearchableField(
        KernelGroupEnvironRow.id,
        UUIDConditions(KernelGroupEnvironRow.id),
        ColumnOrder(KernelGroupEnvironRow.id),
    )
    kernel_group_id = SearchableField(
        KernelGroupEnvironRow.kernel_group_id,
        UUIDConditions(KernelGroupEnvironRow.kernel_group_id),
        ColumnOrder(KernelGroupEnvironRow.kernel_group_id),
    )
    key = SearchableField(
        KernelGroupEnvironRow.key,
        StringConditions(KernelGroupEnvironRow.key),
        ColumnOrder(KernelGroupEnvironRow.key),
    )

    @override
    def to_data(self, row: KernelGroupEnvironRow) -> KernelGroupEnvironData:
        return row.to_data()


class KernelGroupEnvironSearchableFields:
    own = _KernelGroupEnvironOwnFields()
