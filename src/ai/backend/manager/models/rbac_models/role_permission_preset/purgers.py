from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.identifier.role_permission_preset import RolePermissionPresetID
from ai.backend.manager.data.role_preset.types import RolePermissionPresetData
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.specs.purger import FieldPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class RolePermissionPresetPurger(FieldPurger[RolePermissionPresetRow, RolePermissionPresetData]):
    """Purger for one permission entry, authorized through its preset."""

    permission_preset_id: RolePermissionPresetID

    @override
    def row_class(self) -> type[RolePermissionPresetRow]:
        return RolePermissionPresetRow

    @override
    def pk_value(self) -> RolePermissionPresetID:
        return self.permission_preset_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: RolePermissionPresetRow) -> RolePermissionPresetData:
        return row.to_data()
