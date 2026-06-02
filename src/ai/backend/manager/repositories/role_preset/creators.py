from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import (
    EntityType,
    OperationType,
    ScopeType,
)
from ai.backend.common.identifier.role_preset import RolePresetID
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.errors.role_preset import RolePermissionPresetConflict
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.repositories.base.creator import (
    CreatorSpec,
    DependentCreatorSpec,
)
from ai.backend.manager.repositories.base.types import IntegrityErrorCheck


@dataclass
class RolePresetCreatorSpec(CreatorSpec[RolePresetRow]):
    name: str
    scope_type: ScopeType
    auto_assign: bool = False

    @override
    def build_row(self) -> RolePresetRow:
        return RolePresetRow(
            name=self.name,
            scope_type=self.scope_type,
            auto_assign=self.auto_assign,
        )


@dataclass
class RolePermissionPresetDependentCreatorSpec(
    DependentCreatorSpec[RolePresetID, RolePermissionPresetRow]
):
    entity_type: EntityType
    operation: OperationType

    @override
    def build_row(self, dependency: RolePresetID) -> RolePermissionPresetRow:
        return RolePermissionPresetRow(
            role_preset_id=dependency,
            entity_type=self.entity_type,
            operation=self.operation,
        )

    @property
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


@dataclass
class RolePermissionPresetCreatorSpec(CreatorSpec[RolePermissionPresetRow]):
    role_preset_id: RolePresetID
    entity_type: EntityType
    operation: OperationType

    @override
    def build_row(self) -> RolePermissionPresetRow:
        return RolePermissionPresetRow(
            role_preset_id=self.role_preset_id,
            entity_type=self.entity_type,
            operation=self.operation,
        )

    @property
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
