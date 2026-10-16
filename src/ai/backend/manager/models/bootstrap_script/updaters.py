from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.bootstrap_script import BootstrapScript, BootstrapScriptID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.bootstrap_script.types import BootstrapScriptData
from ai.backend.manager.models.bootstrap_script.row import BootstrapScriptRow
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataBatchUpdater, DataUpdater
from ai.backend.manager.types import OptionalState


@dataclass
class DefaultBootstrapScriptUpdater(DataBatchUpdater[BootstrapScriptRow, BootstrapScriptData]):
    """Rewrites the script of the entity's default bootstrap script."""

    entity: EntityIdentifier
    script: BootstrapScript

    @property
    @override
    def row_class(self) -> type[BootstrapScriptRow]:
        return BootstrapScriptRow

    @override
    def conditions(self) -> list[QueryCondition]:
        return [
            lambda: BootstrapScriptRow.entity_type == self.entity.entity_type(),
            lambda: BootstrapScriptRow.entity_id == self.entity,
            lambda: BootstrapScriptRow.is_default.is_(True),
        ]

    @override
    def build_values(self) -> dict[str, Any]:
        return {"script": self.script}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: BootstrapScriptRow) -> BootstrapScriptData:
        return row.to_data()


@dataclass
class BootstrapScriptContentUpdater(DataUpdater[BootstrapScriptRow, BootstrapScriptData]):
    """Rewrites the script of one bootstrap script."""

    script_id: BootstrapScriptID
    script: OptionalState[BootstrapScript]

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
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.script.update_dict(to_update, "script")
        return to_update

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: BootstrapScriptRow) -> BootstrapScriptData:
        return row.to_data()


@dataclass
class MarkDefaultBootstrapScriptUpdater(DataUpdater[BootstrapScriptRow, BootstrapScriptData]):
    """Marks one bootstrap script as its entity's default. The previous mark must be
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
    def build_values(self) -> dict[str, Any]:
        return {"is_default": True}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: BootstrapScriptRow) -> BootstrapScriptData:
        return row.to_data()


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
        return row.to_data()
