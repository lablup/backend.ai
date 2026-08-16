from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.identifier.role_preset import RolePresetID
from ai.backend.manager.data.permission.types import EntityType, OperationType
from ai.backend.manager.data.role_preset.types import RolePermissionPresetData
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.errors.role_preset import RolePermissionPresetConflict
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.specs.creator import FieldCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class RolePermissionPresetCreator(
    FieldCreator[RolePresetID, RolePermissionPresetRow, RolePermissionPresetData]
):
    """Creator for one permission entry of a role preset.

    A field of its preset: it grants nothing of its own and dies with the preset. The
    owner id arrives at build time, so the rows precede the preset's existence.
    """

    entity_type: EntityType
    operation: OperationType

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=RolePermissionPresetConflict(
                    f"Duplicate permission entry ({self.entity_type}, {self.operation})."
                ),
            ),
        )

    @override
    def build_row(self, owner_id: RolePresetID) -> RolePermissionPresetRow:
        return RolePermissionPresetRow(
            role_preset_id=owner_id,
            entity_type=self.entity_type,
            operation=self.operation,
        )

    @override
    def to_data(self, row: RolePermissionPresetRow) -> RolePermissionPresetData:
        return row.to_data()
