from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.dotfile.row import DotfileRow
from ai.backend.manager.models.scopes import ExistenceCheck, ScopeTarget


@dataclass(frozen=True)
class UserDotfileTarget(ScopeTarget):
    """The dotfiles one user owns."""

    user_id: UserID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.user_id

    @override
    def to_condition(self) -> QueryCondition:
        user_id = self.user_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                DotfileRow.entity_type == user_id.entity_type(), DotfileRow.entity_id == user_id
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        # The action's scope gate already answered for the user.
        return ()
