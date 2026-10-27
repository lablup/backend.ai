"""What a bootstrap script search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.common.data.entity.types import RuntimeEntityID
from ai.backend.manager.data.bootstrap_script.types import BootstrapScriptData
from ai.backend.manager.models.bootstrap_script.row import BootstrapScriptRow
from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField


class _BootstrapScriptOwnFields(RowDataConverter[BootstrapScriptRow, BootstrapScriptData]):
    """The script's own columns; its content is in ``bootstrap_script_revisions``."""

    field_id = SearchableField(
        BootstrapScriptRow.id,
        UUIDConditions(BootstrapScriptRow.id),
        ColumnOrder(BootstrapScriptRow.id),
    )
    entity_type = SearchableField(
        BootstrapScriptRow.entity_type,
        StringConditions(BootstrapScriptRow.entity_type),
        ColumnOrder(BootstrapScriptRow.entity_type),
    )
    entity_id = SearchableField(
        BootstrapScriptRow.entity_id,
        UUIDConditions(BootstrapScriptRow.entity_id),
        ColumnOrder(BootstrapScriptRow.entity_id),
    )
    is_default = SearchableField(
        BootstrapScriptRow.is_default,
        BoolConditions(BootstrapScriptRow.is_default),
        ColumnOrder(BootstrapScriptRow.is_default),
    )
    created_at = SearchableField(
        BootstrapScriptRow.created_at,
        DateTimeConditions(BootstrapScriptRow.created_at),
        ColumnOrder(BootstrapScriptRow.created_at),
    )
    deleted_at = SearchableField(
        BootstrapScriptRow.deleted_at,
        DateTimeConditions(BootstrapScriptRow.deleted_at),
        ColumnOrder(BootstrapScriptRow.deleted_at),
    )

    @override
    def to_data(self, row: BootstrapScriptRow) -> BootstrapScriptData:
        return BootstrapScriptData(
            id=self.field_id.read(row),
            entity=RuntimeEntityID(self.entity_type.read(row), self.entity_id.read(row)),
            is_default=self.is_default.read(row),
            created_at=self.created_at.read(row),
            deleted_at=self.deleted_at.read(row),
        )


class BootstrapScriptSearchableFields:
    own = _BootstrapScriptOwnFields()
