from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.bootstrap_script import BootstrapScriptID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.data.bootstrap_script.types import BootstrapScriptData
from ai.backend.manager.models.bootstrap_script.row import BootstrapScriptRow
from ai.backend.manager.models.specs.querier import (
    BulkFieldQuerier,
    FieldQuerier,
    OwnedFieldQuerier,
)


@dataclass
class BootstrapScriptQuerier(
    OwnedFieldQuerier[EntityIdentifier, BootstrapScriptRow, BootstrapScriptData]
):
    """The script a session of each entity runs: its default, else the oldest one."""

    entity_type: EntityType

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return (
            sa.select(BootstrapScriptRow)
            .where(BootstrapScriptRow.entity_type == self.entity_type)
            .distinct(BootstrapScriptRow.entity_id)
            .order_by(
                BootstrapScriptRow.entity_id,
                BootstrapScriptRow.is_default.desc(),
                BootstrapScriptRow.created_at.asc(),
                BootstrapScriptRow.id.asc(),
            )
        )

    @override
    def owner_id_column(self) -> InstrumentedAttribute[Any]:
        return BootstrapScriptRow.entity_id

    @override
    def to_data(self, row: BootstrapScriptRow) -> BootstrapScriptData:
        return row.to_data()


@dataclass
class BootstrapScriptByIdQuerier(FieldQuerier[BootstrapScriptRow, BootstrapScriptData]):
    script_id: BootstrapScriptID

    @override
    def row_class(self) -> type[BootstrapScriptRow]:
        return BootstrapScriptRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return BootstrapScriptRow.id

    @override
    def target_id_value(self) -> BootstrapScriptID:
        return self.script_id

    @override
    def to_data(self, row: BootstrapScriptRow) -> BootstrapScriptData:
        return row.to_data()


class BulkBootstrapScriptQuerier(BulkFieldQuerier[BootstrapScriptRow, BootstrapScriptData]):
    @override
    def row_class(self) -> type[BootstrapScriptRow]:
        return BootstrapScriptRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return BootstrapScriptRow.id

    @override
    def to_data(self, row: BootstrapScriptRow) -> BootstrapScriptData:
        return row.to_data()
