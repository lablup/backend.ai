"""What a bootstrap script search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.common.data.entity.types import RuntimeEntityID
from ai.backend.manager.data.bootstrap_script.types import (
    BootstrapScriptData,
    UserDefaultBootstrapScriptData,
)
from ai.backend.manager.models.bootstrap_script.row import (
    BootstrapScriptRow,
    UserDefaultBootstrapScriptRow,
)
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
            created_at=self.created_at.read(row),
            deleted_at=self.deleted_at.read(row),
        )


class _UserDefaultBootstrapScriptOwnFields(
    RowDataConverter[UserDefaultBootstrapScriptRow, UserDefaultBootstrapScriptData]
):
    user_id = SearchableField(
        UserDefaultBootstrapScriptRow.user_id,
        UUIDConditions(UserDefaultBootstrapScriptRow.user_id),
        ColumnOrder(UserDefaultBootstrapScriptRow.user_id),
    )
    script_id = SearchableField(
        UserDefaultBootstrapScriptRow.script_id,
        UUIDConditions(UserDefaultBootstrapScriptRow.script_id),
        ColumnOrder(UserDefaultBootstrapScriptRow.script_id),
    )

    @override
    def to_data(self, row: UserDefaultBootstrapScriptRow) -> UserDefaultBootstrapScriptData:
        return UserDefaultBootstrapScriptData(
            user_id=self.user_id.read(row),
            script_id=self.script_id.read(row),
        )


class BootstrapScriptSearchableFields:
    own = _BootstrapScriptOwnFields()
    user_default = _UserDefaultBootstrapScriptOwnFields()
