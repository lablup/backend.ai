from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.bootstrap_script import BootstrapScript, BootstrapScriptID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.bootstrap_script.types import BootstrapScriptData
from ai.backend.manager.models.bootstrap_script.row import BootstrapScriptRow
from ai.backend.manager.models.bootstrap_script.searchable_fields import (
    BootstrapScriptSearchableFields,
)
from ai.backend.manager.models.specs.creator import FieldCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class BootstrapScriptCreator(
    FieldCreator[EntityIdentifier, BootstrapScriptRow, BootstrapScriptData]
):
    script: BootstrapScript
    is_default: bool

    @override
    def field_id(self, row: BootstrapScriptRow) -> BootstrapScriptID:
        return row.id

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self, owner_id: EntityIdentifier) -> BootstrapScriptRow:
        return BootstrapScriptRow(
            entity_type=owner_id.entity_type(),
            entity_id=owner_id,
            script=self.script,
            is_default=self.is_default,
        )

    @override
    def to_data(self, row: BootstrapScriptRow) -> BootstrapScriptData:
        return BootstrapScriptSearchableFields.own.to_data(row)
