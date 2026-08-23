"""Operation scopes for error logs."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.error_log.row import ErrorLogRow
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope

__all__ = ("UserErrorLogOperationScope",)


@dataclass(frozen=True)
class UserErrorLogOperationScope(OperationScope):
    """The errors one user may see.

    Cleared rows drop out here rather than in the searcher: clearing is this domain's
    soft delete, and the global read still returns them.

    ``existence_checks`` is empty by convention -- RBAC validation already gates
    reachability.
    """

    user_id: uuid.UUID

    @override
    def to_condition(self) -> QueryCondition:
        user_id = self.user_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(ErrorLogRow.user == user_id, ~ErrorLogRow.is_cleared)

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()
