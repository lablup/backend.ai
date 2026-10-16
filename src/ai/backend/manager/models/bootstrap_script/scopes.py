"""Operation scopes for bootstrap scripts."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.bootstrap_script.row import BootstrapScriptRow
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.scopes import ExistenceCheck, ScopeTarget
from ai.backend.manager.models.user.row import UserRow

__all__ = ("UserBootstrapScriptTarget",)


@dataclass(frozen=True)
class UserBootstrapScriptTarget(ScopeTarget):
    """The bootstrap scripts set on one user."""

    user_id: UUID

    @override
    def scope_id(self) -> EntityIdentifier:
        return UserID(self.user_id)

    @override
    def to_condition(self) -> QueryCondition:
        user_id = self.user_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                BootstrapScriptRow.entity_type == UserEntityType(),
                BootstrapScriptRow.entity_id == user_id,
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[UUID]]:
        return [
            ExistenceCheck(
                column=UserRow.uuid,
                value=self.user_id,
                error=UserNotFound(f"User {self.user_id} not found"),
            ),
        ]
