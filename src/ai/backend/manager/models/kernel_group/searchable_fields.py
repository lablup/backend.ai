"""What a kernel group search can filter and order by, and how a group row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.manager.data.kernel_group.types import KernelGroupData
from ai.backend.manager.models.kernel_group.row import KernelGroupRow
from ai.backend.manager.models.kernel_group_environ.row import KernelGroupEnvironRow
from ai.backend.manager.models.kernel_group_environ.searchable_fields import (
    KernelGroupEnvironSearchableFields,
)
from ai.backend.manager.models.kernel_group_resource_slot.row import KernelGroupResourceSlotRow
from ai.backend.manager.models.kernel_group_resource_slot.searchable_fields import (
    KernelGroupResourceSlotSearchableFields,
)
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.correlation import ToManyCorrelation
from ai.backend.manager.models.specs.search.field import NestedSearchableField, SearchableField


class _KernelGroupOwnFields(RowDataConverter[KernelGroupRow, KernelGroupData]):
    """The kernel group's own columns."""

    field_id = SearchableField(
        KernelGroupRow.id, UUIDConditions(KernelGroupRow.id), ColumnOrder(KernelGroupRow.id)
    )
    session_id = SearchableField(
        KernelGroupRow.session_id,
        UUIDConditions(KernelGroupRow.session_id),
        ColumnOrder(KernelGroupRow.session_id),
    )
    role = SearchableField(
        KernelGroupRow.role,
        StringConditions(KernelGroupRow.role),
        ColumnOrder(KernelGroupRow.role),
    )
    image_id = SearchableField(
        KernelGroupRow.image_id,
        UUIDConditions(KernelGroupRow.image_id),
        ColumnOrder(KernelGroupRow.image_id),
    )
    requested_starts_at = SearchableField(
        KernelGroupRow.requested_starts_at,
        DateTimeConditions(KernelGroupRow.requested_starts_at),
        ColumnOrder(KernelGroupRow.requested_starts_at),
    )
    created_at = SearchableField(
        KernelGroupRow.created_at,
        DateTimeConditions(KernelGroupRow.created_at),
        ColumnOrder(KernelGroupRow.created_at),
    )

    @override
    def to_data(self, row: KernelGroupRow) -> KernelGroupData:
        return row.to_data()


class _KernelGroupNestedFields:
    """The rows the kernel group owns. Read under the kernel group's own permission."""

    environ = NestedSearchableField(
        KernelGroupEnvironSearchableFields.own,
        ToManyCorrelation(
            KernelGroupEnvironRow,
            KernelGroupRow,
            KernelGroupEnvironRow.kernel_group_id == KernelGroupRow.id,
        ),
    )
    resource_slots = NestedSearchableField(
        KernelGroupResourceSlotSearchableFields.own,
        ToManyCorrelation(
            KernelGroupResourceSlotRow,
            KernelGroupRow,
            KernelGroupResourceSlotRow.kernel_group_id == KernelGroupRow.id,
        ),
    )


class KernelGroupSearchableFields:
    own = _KernelGroupOwnFields()
    nested = _KernelGroupNestedFields
