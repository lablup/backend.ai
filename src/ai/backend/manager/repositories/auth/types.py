"""Search scope types for login session and login history queries."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.exception import UserNotFound
from ai.backend.manager.models.login_session.row import LoginHistoryRow, LoginSessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.base.types import ExistenceCheck, QueryCondition, SearchScope


@dataclass(frozen=True)
class MyLoginSessionSearchScope(SearchScope):
    """Scope for searching login sessions owned by the current user."""

    user_id: UUID

    def to_condition(self) -> QueryCondition:
        user_id = self.user_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return LoginSessionRow.user_id == user_id

        return inner

    @property
    def existence_checks(self) -> Sequence[ExistenceCheck[UUID]]:
        return [
            ExistenceCheck(
                column=UserRow.uuid,
                value=self.user_id,
                error=UserNotFound(extra_data={"user_id": str(self.user_id)}),
            ),
        ]


@dataclass(frozen=True)
class MyLoginHistorySearchScope(SearchScope):
    """Scope for searching login history of the current user."""

    user_id: UUID

    def to_condition(self) -> QueryCondition:
        user_id = self.user_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return LoginHistoryRow.user_id == user_id

        return inner

    @property
    def existence_checks(self) -> Sequence[ExistenceCheck[UUID]]:
        return [
            ExistenceCheck(
                column=UserRow.uuid,
                value=self.user_id,
                error=UserNotFound(extra_data={"user_id": str(self.user_id)}),
            ),
        ]
