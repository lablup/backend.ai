"""What a bootstrap script revision search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.common.data.entity.bootstrap_script import BootstrapScript
from ai.backend.manager.data.bootstrap_script.types import BootstrapScriptRevisionData
from ai.backend.manager.models.bootstrap_script_revision.row import BootstrapScriptRevisionRow
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.integer import IntConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField


class _BootstrapScriptRevisionOwnFields(
    RowDataConverter[BootstrapScriptRevisionRow, BootstrapScriptRevisionData]
):
    """The revision's own columns; the script body is user-written, so it is neither filtered nor ordered."""

    field_id = SearchableField(
        BootstrapScriptRevisionRow.id,
        UUIDConditions(BootstrapScriptRevisionRow.id),
        ColumnOrder(BootstrapScriptRevisionRow.id),
    )
    script_id = SearchableField(
        BootstrapScriptRevisionRow.script_id,
        UUIDConditions(BootstrapScriptRevisionRow.script_id),
        ColumnOrder(BootstrapScriptRevisionRow.script_id),
    )
    revision_number = SearchableField(
        BootstrapScriptRevisionRow.revision_number,
        IntConditions(BootstrapScriptRevisionRow.revision_number),
        ColumnOrder(BootstrapScriptRevisionRow.revision_number),
    )
    script = SearchableField(BootstrapScriptRevisionRow.script, None, None)
    creator_id = SearchableField(
        BootstrapScriptRevisionRow.creator_id,
        UUIDConditions(BootstrapScriptRevisionRow.creator_id),
        ColumnOrder(BootstrapScriptRevisionRow.creator_id),
    )
    created_at = SearchableField(
        BootstrapScriptRevisionRow.created_at,
        DateTimeConditions(BootstrapScriptRevisionRow.created_at),
        ColumnOrder(BootstrapScriptRevisionRow.created_at),
    )

    @override
    def to_data(self, row: BootstrapScriptRevisionRow) -> BootstrapScriptRevisionData:
        return BootstrapScriptRevisionData(
            id=self.field_id.read(row),
            script_id=self.script_id.read(row),
            revision_number=self.revision_number.read(row),
            script=BootstrapScript(self.script.read(row)),
            creator_id=self.creator_id.read(row),
            created_at=self.created_at.read(row),
        )


class BootstrapScriptRevisionSearchableFields:
    own = _BootstrapScriptRevisionOwnFields()
