"""What a dotfile application search can filter and order by, and how its row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.common.data.entity.types import RuntimeEntityID
from ai.backend.manager.data.dotfile.types import DotfileApplicationData
from ai.backend.manager.models.dotfile_application.row import DotfileApplicationRow
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField


class _DotfileApplicationOwnFields(RowDataConverter[DotfileApplicationRow, DotfileApplicationData]):
    entity_type = SearchableField(
        DotfileApplicationRow.entity_type,
        StringConditions(DotfileApplicationRow.entity_type),
        ColumnOrder(DotfileApplicationRow.entity_type),
    )
    entity_id = SearchableField(
        DotfileApplicationRow.entity_id,
        UUIDConditions(DotfileApplicationRow.entity_id),
        ColumnOrder(DotfileApplicationRow.entity_id),
    )
    path = SearchableField(
        DotfileApplicationRow.path,
        StringConditions(DotfileApplicationRow.path),
        ColumnOrder(DotfileApplicationRow.path),
    )
    perm = SearchableField(DotfileApplicationRow.perm, None, None)
    dotfile_id = SearchableField(
        DotfileApplicationRow.dotfile_id,
        UUIDConditions(DotfileApplicationRow.dotfile_id),
        ColumnOrder(DotfileApplicationRow.dotfile_id),
    )

    @override
    def to_data(self, row: DotfileApplicationRow) -> DotfileApplicationData:
        return DotfileApplicationData(
            entity=RuntimeEntityID(self.entity_type.read(row), self.entity_id.read(row)),
            path=self.path.read(row),
            perm=self.perm.read(row),
            dotfile_id=self.dotfile_id.read(row),
        )


class DotfileApplicationSearchableFields:
    own = _DotfileApplicationOwnFields()
