"""What a system session environ search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironID
from ai.backend.common.data.system_session_environ.types import (
    SystemSessionEnvironScopeType,
    SystemSessionEnvironValueSource,
)
from ai.backend.manager.data.system_session_environ.types import SystemSessionEnvironData
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField
from ai.backend.manager.models.system_session_environ.row import SystemSessionEnvironRow


class _SystemSessionEnvironOwnFields(
    RowDataConverter[SystemSessionEnvironRow, SystemSessionEnvironData]
):
    """The system session environ's own columns."""

    id = SearchableField(
        SystemSessionEnvironRow.id,
        UUIDConditions(SystemSessionEnvironRow.id),
        ColumnOrder(SystemSessionEnvironRow.id),
    )
    value_source = SearchableField(
        SystemSessionEnvironRow.value_source,
        EnumConditions(SystemSessionEnvironRow.value_source, SystemSessionEnvironValueSource),
        ColumnOrder(SystemSessionEnvironRow.value_source),
    )
    key = SearchableField(
        SystemSessionEnvironRow.key,
        StringConditions(SystemSessionEnvironRow.key),
        ColumnOrder(SystemSessionEnvironRow.key),
    )
    scope_type = SearchableField(
        SystemSessionEnvironRow.scope_type,
        EnumConditions(SystemSessionEnvironRow.scope_type, SystemSessionEnvironScopeType),
        ColumnOrder(SystemSessionEnvironRow.scope_type),
    )
    scope_id = SearchableField(
        SystemSessionEnvironRow.scope_id,
        UUIDConditions(SystemSessionEnvironRow.scope_id),
        ColumnOrder(SystemSessionEnvironRow.scope_id),
    )
    created_at = SearchableField(
        SystemSessionEnvironRow.created_at,
        DateTimeConditions(SystemSessionEnvironRow.created_at),
        ColumnOrder(SystemSessionEnvironRow.created_at),
    )
    updated_at = SearchableField(
        SystemSessionEnvironRow.updated_at,
        DateTimeConditions(SystemSessionEnvironRow.updated_at),
        ColumnOrder(SystemSessionEnvironRow.updated_at),
    )
    deleted_at = SearchableField(
        SystemSessionEnvironRow.deleted_at,
        DateTimeConditions(SystemSessionEnvironRow.deleted_at),
        ColumnOrder(SystemSessionEnvironRow.deleted_at),
    )

    @override
    def to_data(self, row: SystemSessionEnvironRow) -> SystemSessionEnvironData:
        return SystemSessionEnvironData(
            id=SystemSessionEnvironID(self.id.read(row)),
            value_source=self.value_source.read(row),
            key=self.key.read(row),
            scope_id=self.scope_type.read(row).to_owner(self.scope_id.read(row)),
            created_at=self.created_at.read(row),
            updated_at=self.updated_at.read(row),
            deleted_at=self.deleted_at.read(row),
        )


class SystemSessionEnvironSearchableFields:
    own = _SystemSessionEnvironOwnFields()
