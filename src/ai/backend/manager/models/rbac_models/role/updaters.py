"""DataUpdater implementations for the role repository.

The ``status`` column is split off from the general updater, so the ordinary edit
path has no field to make the transition with (`models/specs/AGENTS.md`).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.role import RoleID
from ai.backend.manager.data.permission.role import RoleData
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import RoleSource
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.rbac_models.role.conditions import RoleConditions
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater, GuardedDataUpdater
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class RoleUpdater(GuardedDataUpdater[RoleRow, RoleData]):
    """Edits a role's declaration. Carries no ``status`` field.

    Declines a SYSTEM role: its declaration belongs to the role preset.
    """

    role_id: RoleID
    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    description: TriState[str] = field(default_factory=TriState[str].nop)
    auto_assign: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)

    @property
    @override
    def row_class(self) -> type[RoleRow]:
        return RoleRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return RoleRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.role_id

    @override
    def guard_conditions(self) -> list[QueryCondition]:
        return [RoleConditions.by_source_equals(RoleSource.CUSTOM)]

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
        return to_update

    @override
    def to_data(self, row: RoleRow) -> RoleData:
        return row.to_data()


@dataclass
class RoleSoftDeleteUpdater(GuardedDataUpdater[RoleRow, RoleData]):
    """Marks a role deleted; the values are constants so they cannot be passed wrong.

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
    def target_id_value(self) -> UUID:
        return self.role_id

    @override
    def guard_conditions(self) -> list[QueryCondition]:
        return [RoleConditions.by_source_equals(RoleSource.CUSTOM)]

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        return {"status": RoleStatus.DELETED, "deleted_at": sa.func.now()}

    @override
    def to_data(self, row: RoleRow) -> RoleData:
        return row.to_data()


@dataclass
class RoleRestoreUpdater(DataUpdater[RoleRow, RoleData]):
    """Undoes the soft delete; the mirror of :class:`RoleSoftDeleteUpdater`."""

    role_id: RoleID

    @property
    @override
    def row_class(self) -> type[RoleRow]:
        return RoleRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return RoleRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.role_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        return {"status": RoleStatus.ACTIVE, "deleted_at": None}

    @override
    def to_data(self, row: RoleRow) -> RoleData:
        return row.to_data()
