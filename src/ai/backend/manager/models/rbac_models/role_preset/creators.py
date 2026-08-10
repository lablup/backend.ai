from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.manager.data.permission.types import ScopeType
from ai.backend.manager.data.role_preset.types import RolePresetData
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.specs.creator import GlobalEntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class RolePresetCreator(GlobalEntityCreator[RolePresetRow, RolePresetData]):
    """Creator for a role preset — the global catalog of roles a scope type provisions.

    Global rather than entity: a preset declares which roles a scope type gets, it
    governs no entities of its own and lives outside the scope hierarchy. Its
    permission rows hang off it as fields.
    """

    name: str
    scope_type: ScopeType
    auto_assign: bool = False
    role_name_template: str | None = None

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self) -> RolePresetRow:
        return RolePresetRow(
            name=self.name,
            role_name_template=self.role_name_template,
            scope_type=self.scope_type,
            auto_assign=self.auto_assign,
        )

    @override
    def to_data(self, row: RolePresetRow) -> RolePresetData:
        return row.to_data()
