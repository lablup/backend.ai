"""Operation scopes for role assignment rows."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.errors.permission import RoleNotFound
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope

__all__ = (
    "RoleRoleAssignmentTarget",
    "UserRoleAssignmentTarget",
)


@dataclass(frozen=True)
class UserRoleAssignmentTarget(OperationScope):
    """The assignment rows of the roles one user holds."""

    user_id: UserID

    @override
    def to_condition(self) -> QueryCondition:
        user_id = self.user_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserRoleRow.user_id == user_id

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return []


@dataclass(frozen=True)
class RoleRoleAssignmentTarget(OperationScope):
    """The assignment rows of the users holding one role."""

    role_id: RoleID

    @override
    def to_condition(self) -> QueryCondition:
        role_id = self.role_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserRoleRow.role_id == role_id

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return [
            ExistenceCheck(
                column=RoleRow.id,
                value=self.role_id,
                error=RoleNotFound(str(self.role_id)),
            ),
        ]
