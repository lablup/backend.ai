"""Insert spec for bootstrap script revisions."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.bootstrap_script import BootstrapScript, BootstrapScriptID
from ai.backend.common.data.entity.bootstrap_script_revision import BootstrapScriptRevisionID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.bootstrap_script.types import BootstrapScriptRevisionData
from ai.backend.manager.models.bootstrap_script_revision.row import BootstrapScriptRevisionRow
from ai.backend.manager.models.bootstrap_script_revision.searchable_fields import (
    BootstrapScriptRevisionSearchableFields,
)
from ai.backend.manager.models.specs.creator import DanglingFieldCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class BootstrapScriptRevisionCreator(
    DanglingFieldCreator[BootstrapScriptRevisionRow, BootstrapScriptRevisionData]
):
    script_id: BootstrapScriptID
    revision_number: int
    script: BootstrapScript
    creator_id: UserID | None

    @override
    def build_row(self) -> BootstrapScriptRevisionRow:
        return BootstrapScriptRevisionRow(
            script_id=self.script_id,
            revision_number=self.revision_number,
            script=self.script,
            creator_id=self.creator_id,
        )

    @override
    def field_id(self, row: BootstrapScriptRevisionRow) -> BootstrapScriptRevisionID:
        return row.id

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: BootstrapScriptRevisionRow) -> BootstrapScriptRevisionData:
        return BootstrapScriptRevisionSearchableFields.own.to_data(row)
