from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.permission import PermissionID
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.specs.purger import FieldPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class RolePermissionPurger(FieldPurger[PermissionRow, PermissionData]):
    """Purger for one permission entry, authorized through its role. The paths the
    entry is scoped to follow by FK cascade."""

    permission_id: PermissionID

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
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: PermissionRow) -> PermissionData:
        return row.to_data()
