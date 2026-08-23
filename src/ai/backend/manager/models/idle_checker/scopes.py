"""Operation scopes for idle checkers."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.permission.types import ScopeType
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.idle_checker.row import IdleCheckerBindingRow
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope


@dataclass(frozen=True)
class IdleCheckerAssignmentOperationScope(OperationScope):
    """Idle checker bindings attached to one ``(scope_type, scope_id)`` pair.

    One scope = one item of a scoped binding query; the repository layer
    combines multiple scopes with ``OR`` to realize the ``IdleCheckerAssignmentScope``
    union semantics.

    ``existence_checks`` is empty by ``SearchableActionTarget`` convention —
    RBAC validation already gates scope reachability.
    """

    scope_type: ScopeType
    scope_id: uuid.UUID

    @override
    def to_condition(self) -> QueryCondition:
        scope_type = self.scope_type
        scope_id = self.scope_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                IdleCheckerBindingRow.scope_type == scope_type,
                IdleCheckerBindingRow.scope_id == scope_id,
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()
