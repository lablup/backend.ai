from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.permission import PermissionID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.data.permission.bit import single_bit
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.role_preset import SystemRoleNotEditable
from ai.backend.manager.models.rbac_models.permission.conditions import PermissionConditions
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.permission.searchable_fields import (
    PermissionSearchableFields,
)
from ai.backend.manager.models.specs.types import GuardCheck, IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import GuardedDataUpdater
from ai.backend.manager.types import OptionalState


@dataclass
class RolePermissionUpdater(GuardedDataUpdater[PermissionRow, PermissionData]):
    """Updater for one permission entry of a role. Declines an entry of a SYSTEM role."""

    permission_id: PermissionID
    entity_type: OptionalState[EntityType] = field(default_factory=OptionalState.nop)
    permission: OptionalState[Permission] = field(default_factory=OptionalState.nop)

    @property
    @override
    def row_class(self) -> type[PermissionRow]:
        return PermissionRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return PermissionRow.id

    @override
    def target_id_value(self) -> PermissionID:
        return self.permission_id

    @override
    def guard_checks(self) -> Sequence[GuardCheck]:
        return (
            GuardCheck(
                condition=PermissionConditions.by_custom_role(),
                error=SystemRoleNotEditable(
                    f"Permission {self.permission_id} belongs to a SYSTEM role."
                ),
            ),
        )

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.entity_type.update_dict(to_update, "entity_type")
        if (permission := self.permission.optional_value()) is not None:
            to_update["permission"] = single_bit(permission)
        return to_update

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: PermissionRow) -> PermissionData:
        return PermissionSearchableFields.own.to_data(row)
