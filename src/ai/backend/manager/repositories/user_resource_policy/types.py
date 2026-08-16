"""Types for user resource policy repository operations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.identifier.user import UserID
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.resource_policy.row import UserResourcePolicyRow
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope
from ai.backend.manager.models.user.row import UserRow

__all__ = ("UserResourcePolicyOperationScope",)


@dataclass(frozen=True)
class UserResourcePolicyOperationScope(OperationScope):
    """The policy the named user is subject to.

    The row carries no owner column, so the scope narrows through the user that
    names it.

    ``existence_checks`` is empty by convention -- RBAC validation already gates
    reachability.
    """

    user_id: UserID

    @override
    def to_condition(self) -> QueryCondition:
        user_id = self.user_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserResourcePolicyRow.name.in_(
                sa.select(UserRow.resource_policy).where(UserRow.uuid == user_id)
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()
