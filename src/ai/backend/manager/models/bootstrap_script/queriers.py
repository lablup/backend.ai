from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.bootstrap_script import BootstrapScriptID
from ai.backend.manager.data.bootstrap_script.types import BootstrapScriptData
from ai.backend.manager.models.bootstrap_script.row import BootstrapScriptRow
from ai.backend.manager.models.bootstrap_script.searchable_fields import (
    BootstrapScriptSearchableFields,
)
from ai.backend.manager.models.specs.querier import BulkFieldQuerier, FieldQuerier


@dataclass
class BootstrapScriptQuerier(FieldQuerier[BootstrapScriptRow, BootstrapScriptData]):
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
        return BootstrapScriptSearchableFields.own.to_data(row)


class BulkBootstrapScriptQuerier(BulkFieldQuerier[BootstrapScriptRow, BootstrapScriptData]):
    @override
    def row_class(self) -> type[BootstrapScriptRow]:
        return BootstrapScriptRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return BootstrapScriptRow.id

    @override
    def to_data(self, row: BootstrapScriptRow) -> BootstrapScriptData:
        return BootstrapScriptSearchableFields.own.to_data(row)
