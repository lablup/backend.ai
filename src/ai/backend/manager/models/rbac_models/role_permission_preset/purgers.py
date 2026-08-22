from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.role_permission_preset import RolePermissionPresetID
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
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return RolePermissionPresetRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.permission_preset_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: RolePermissionPresetRow) -> RolePermissionPresetData:
        return row.to_data()
