from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.permission.role import RoleData
from ai.backend.manager.data.permission.types import RoleSource
from ai.backend.manager.errors.role_preset import SystemRoleNotEditable
from ai.backend.manager.models.rbac_models.role.conditions import RoleConditions
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.specs.purger import GuardedEntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck, GuardCheck


@dataclass
class RolePurger(GuardedEntityPurger[RoleRow, RoleData]):
    """Purger for a role. Its permission rows and assignments follow by FK cascade.

    Declines a SYSTEM role: its declaration belongs to the role preset.
    """

    role_id: RoleID

    @override
    def row_class(self) -> type[RoleRow]:
        return RoleRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return RoleRow.id

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.role_id

    @override
    def guard_checks(self) -> Sequence[GuardCheck]:
        return (
            GuardCheck(
                condition=RoleConditions.by_source_equals(RoleSource.CUSTOM),
                error=SystemRoleNotEditable(f"Role {self.role_id} is a SYSTEM role."),
            ),
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: RoleRow) -> RoleData:
        return row.to_data()
