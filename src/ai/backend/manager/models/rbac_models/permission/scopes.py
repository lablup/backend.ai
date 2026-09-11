"""Operation scopes for permissions."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.role import RoleID
from ai.backend.manager.errors.permission import RoleNotFound
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope


@dataclass(frozen=True)
class PermissionOperationScope(OperationScope):
    """Scope for searching scoped permissions by role."""

    role_id: RoleID

    @override
    def to_condition(self) -> QueryCondition:
        role_id = self.role_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return PermissionRow.role_id == role_id

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return [
            ExistenceCheck(
                column=RoleRow.id,
                value=self.role_id,
                error=RoleNotFound(),
            ),
        ]
