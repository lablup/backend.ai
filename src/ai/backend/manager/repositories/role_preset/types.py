"""Operation scopes for the role preset repository."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope

__all__ = ("RolePresetPermissionOperationScope",)


@dataclass(frozen=True)
class RolePresetPermissionOperationScope(OperationScope):
    """The permission entries one preset holds."""

    preset_id: RolePresetID

    @override
    def to_condition(self) -> QueryCondition:
        preset_id = self.preset_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RolePermissionPresetRow.role_preset_id == preset_id

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()
