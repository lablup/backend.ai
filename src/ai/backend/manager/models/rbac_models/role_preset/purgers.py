from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.identifier.role_preset import RolePresetID
from ai.backend.manager.data.role_preset.types import RolePresetData
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.specs.purger import GlobalEntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class RolePresetPurger(GlobalEntityPurger[RolePresetRow, RolePresetData]):
    """Purger for a role preset. Its permission rows follow by FK cascade."""

    preset_id: RolePresetID

    @override
    def row_class(self) -> type[RolePresetRow]:
        return RolePresetRow

    @override
    def pk_value(self) -> RolePresetID:
        return self.preset_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: RolePresetRow) -> RolePresetData:
        return row.to_data()
