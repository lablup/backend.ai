"""What a dotfile revision search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.manager.data.dotfile.types import DotfileRevisionData
from ai.backend.manager.models.dotfile_revision.row import DotfileRevisionRow
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.integer import IntConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField


class _DotfileRevisionOwnFields(RowDataConverter[DotfileRevisionRow, DotfileRevisionData]):
    """The revision's own columns; the file body cannot be filtered or ordered."""

    field_id = SearchableField(
        DotfileRevisionRow.id,
        UUIDConditions(DotfileRevisionRow.id),
        ColumnOrder(DotfileRevisionRow.id),
    )
    dotfile_id = SearchableField(
        DotfileRevisionRow.dotfile_id,
        UUIDConditions(DotfileRevisionRow.dotfile_id),
        ColumnOrder(DotfileRevisionRow.dotfile_id),
    )
    revision_number = SearchableField(
        DotfileRevisionRow.revision_number,
        IntConditions(DotfileRevisionRow.revision_number),
        ColumnOrder(DotfileRevisionRow.revision_number),
    )
    perm = SearchableField(DotfileRevisionRow.perm, None, None)
    data = SearchableField(DotfileRevisionRow.data, None, None)
    creator_id = SearchableField(
        DotfileRevisionRow.creator_id,
        UUIDConditions(DotfileRevisionRow.creator_id),
        ColumnOrder(DotfileRevisionRow.creator_id),
    )
    created_at = SearchableField(
        DotfileRevisionRow.created_at,
        DateTimeConditions(DotfileRevisionRow.created_at),
        ColumnOrder(DotfileRevisionRow.created_at),
    )

    @override
    def to_data(self, row: DotfileRevisionRow) -> DotfileRevisionData:
        return DotfileRevisionData(
            id=self.field_id.read(row),
            dotfile_id=self.dotfile_id.read(row),
            revision_number=self.revision_number.read(row),
            perm=self.perm.read(row),
            data=self.data.read(row),
            creator_id=self.creator_id.read(row),
            created_at=self.created_at.read(row),
        )


class DotfileRevisionSearchableFields:
    own = _DotfileRevisionOwnFields()
