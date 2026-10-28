from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.bootstrap_script import BootstrapScriptID
from ai.backend.manager.data.bootstrap_script.types import BootstrapScriptData
from ai.backend.manager.errors.bootstrap_script import BootstrapScriptNotFound
from ai.backend.manager.models.bootstrap_script.row import BootstrapScriptRow
from ai.backend.manager.models.bootstrap_script.searchable_fields import (
    BootstrapScriptSearchableFields,
)
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.types import GuardCheck, IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataBatchUpdater, GuardedDataUpdater


@dataclass
class MarkDefaultBootstrapScriptUpdater(
    GuardedDataUpdater[BootstrapScriptRow, BootstrapScriptData]
):
    """Marks one live bootstrap script as its entity's default. The previous mark must be
    cleared first: the partial unique index allows one per entity."""

    script_id: BootstrapScriptID

    @property
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
    def guard_checks(self) -> Sequence[GuardCheck]:
        return (
            GuardCheck(
                condition=lambda: BootstrapScriptRow.deleted_at.is_(None),
                error=BootstrapScriptNotFound(f"Bootstrap script {self.script_id} not found"),
            ),
        )

    @override
    def build_values(self) -> dict[str, Any]:
        return {"is_default": True}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: BootstrapScriptRow) -> BootstrapScriptData:
        return BootstrapScriptSearchableFields.own.to_data(row)


class ClearDefaultBootstrapScriptUpdater(DataBatchUpdater[BootstrapScriptRow, BootstrapScriptData]):
    """Clears the default mark within the scope it runs in."""

    @property
    @override
    def row_class(self) -> type[BootstrapScriptRow]:
        return BootstrapScriptRow

    @override
    def conditions(self) -> list[QueryCondition]:
        return [lambda: BootstrapScriptRow.is_default.is_(True)]

    @override
    def build_values(self) -> dict[str, Any]:
        return {"is_default": False}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: BootstrapScriptRow) -> BootstrapScriptData:
        return BootstrapScriptSearchableFields.own.to_data(row)
