"""Operation scopes for roles."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope


@dataclass(frozen=True)
class ScopedRoleOperationScope(OperationScope):
    """The roles of a given scope (project, domain, ...)."""

    scope: EntityIdentifier

    @override
    def to_condition(self) -> QueryCondition:
        scope = self.scope

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                RoleRow.scope_type == scope.entity_type(),
                RoleRow.scope_id == scope,
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return []


@dataclass(frozen=True)
class HeldRoleOperationScope(OperationScope):
    """The roles one user holds."""

    user_id: UserID

    @override
    def to_condition(self) -> QueryCondition:
        user_id = self.user_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleRow.id.in_(
                sa.select(UserRoleRow.role_id).where(UserRoleRow.user_id == user_id)
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return []
