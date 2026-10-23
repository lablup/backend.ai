"""DataUpdater implementations for the role repository.

``deleted_at`` is split off from the general updater (`models/specs/AGENTS.md`). Restore is
the shared ``RestoreUpdater`` in ``models/specs/soft_delete.py``.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.role import RoleID
from ai.backend.manager.data.permission.role import RoleData
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import RoleSource
from ai.backend.manager.errors.role_preset import SystemRoleNotEditable
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.role.searchable_fields import RoleSearchableFields
from ai.backend.manager.models.specs.types import GuardCheck, IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import GuardedDataUpdater
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class RoleUpdater(GuardedDataUpdater[RoleRow, RoleData]):
    """Edits a role's declaration and status. Carries no ``deleted_at`` field.

    Declines a SYSTEM role: its declaration belongs to the role preset.
    """

    role_id: RoleID
    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    description: TriState[str] = field(default_factory=TriState[str].nop)
    auto_assign: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    status: OptionalState[RoleStatus] = field(default_factory=OptionalState[RoleStatus].nop)

    @property
    @override
    def row_class(self) -> type[RoleRow]:
        return RoleRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return RoleRow.id

    @override
    def target_id_value(self) -> RoleID:
        return self.role_id

    @override
    def guard_checks(self) -> Sequence[GuardCheck]:
        return (
            GuardCheck(
                condition=RoleSearchableFields.own.source.filter.equals(RoleSource.CUSTOM),
                error=SystemRoleNotEditable(f"Role {self.role_id} is a SYSTEM role."),
            ),
        )

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.description.update_dict(to_update, "description")
        self.auto_assign.update_dict(to_update, "auto_assign")
        self.status.update_dict(to_update, "status")
        return to_update

    @override
    def to_data(self, row: RoleRow) -> RoleData:
        return RoleSearchableFields.own.to_data(row)


@dataclass
class RoleSoftDeleteUpdater(GuardedDataUpdater[RoleRow, RoleData]):
    """Sets ``deleted_at`` as the shared ``SoftDeleteUpdater`` does; ``status`` stays.

    Declines a SYSTEM role, as :class:`RoleUpdater` does.
    """

    role_id: RoleID

    @property
    @override
    def row_class(self) -> type[RoleRow]:
        return RoleRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return RoleRow.id

    @override
    def target_id_value(self) -> RoleID:
        return self.role_id

    @override
    def guard_checks(self) -> Sequence[GuardCheck]:
        return (
            GuardCheck(
                condition=RoleSearchableFields.own.source.filter.equals(RoleSource.CUSTOM),
                error=SystemRoleNotEditable(f"Role {self.role_id} is a SYSTEM role."),
            ),
        )

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        return {"deleted_at": sa.func.now()}

    @override
    def to_data(self, row: RoleRow) -> RoleData:
        return RoleSearchableFields.own.to_data(row)
