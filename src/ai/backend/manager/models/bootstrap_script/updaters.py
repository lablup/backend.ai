from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.bootstrap_script import BootstrapScript
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.bootstrap_script.types import BootstrapScriptData
from ai.backend.manager.models.bootstrap_script.row import BootstrapScriptRow
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataBatchUpdater


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
