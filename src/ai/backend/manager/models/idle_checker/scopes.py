"""Operation scopes for idle checkers."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.idle_checker.row import IdleCheckerBindingRow
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope


@dataclass(frozen=True)
class IdleCheckerAssignmentOperationScope(OperationScope):
    """Idle checker bindings attached to one scope entity.

    One scope = one item of a scoped binding query; the repository layer
    combines multiple scopes with ``OR``.

    ``existence_checks`` is empty: the scope validator already gates reachability.
    """

    scope: EntityIdentifier

    @override
    def to_condition(self) -> QueryCondition:
        scope = self.scope

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                IdleCheckerBindingRow.scope_type == scope.entity_type(),
                IdleCheckerBindingRow.scope_id == scope,
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()
