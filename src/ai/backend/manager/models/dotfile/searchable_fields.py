"""What a dotfile search can filter and order by, and how a dotfile row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.common.data.entity.types import RuntimeEntityID
from ai.backend.manager.data.dotfile.types import DotfileData
from ai.backend.manager.models.dotfile.row import DotfileRow
from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField


class _DotfileOwnFields(RowDataConverter[DotfileRow, DotfileData]):
    """The dotfile's own columns; the file body cannot be filtered or ordered."""

    field_id = SearchableField(
        DotfileRow.id, UUIDConditions(DotfileRow.id), ColumnOrder(DotfileRow.id)
    )
    entity_type = SearchableField(
        DotfileRow.entity_type,
        StringConditions(DotfileRow.entity_type),
        ColumnOrder(DotfileRow.entity_type),
    )
    entity_id = SearchableField(
        DotfileRow.entity_id,
        UUIDConditions(DotfileRow.entity_id),
        ColumnOrder(DotfileRow.entity_id),
    )
    path = SearchableField(
        DotfileRow.path, StringConditions(DotfileRow.path), ColumnOrder(DotfileRow.path)
    )
    perm = SearchableField(DotfileRow.perm, None, None)
    data = SearchableField(DotfileRow.data, None, None)
    is_default = SearchableField(
        DotfileRow.is_default,
        BoolConditions(DotfileRow.is_default),
        ColumnOrder(DotfileRow.is_default),
    )
    created_at = SearchableField(
        DotfileRow.created_at,
        DateTimeConditions(DotfileRow.created_at),
        ColumnOrder(DotfileRow.created_at),
    )

    @override
    def to_data(self, row: DotfileRow) -> DotfileData:
        return DotfileData(
            id=self.field_id.read(row),
            entity=RuntimeEntityID(self.entity_type.read(row), self.entity_id.read(row)),
            path=self.path.read(row),
            perm=self.perm.read(row),
            data=self.data.read(row),
            is_default=self.is_default.read(row),
        )


class DotfileSearchableFields:
    own = _DotfileOwnFields()
