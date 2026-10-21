from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope
from ai.backend.manager.models.system_session_environ.conditions import (
    SystemSessionEnvironConditions,
)

__all__ = ("SessionSystemSessionEnvironScope",)


@dataclass(frozen=True)
class SessionSystemSessionEnvironScope(OperationScope):
    """The rows one session receives: ``public``, its domain's and its project's.

    Not a :class:`ScopeTarget`: the launcher reads these rows with no caller to authorize.
    """

    domain_id: DomainID
    project_id: ProjectID

    @override
    def to_condition(self) -> QueryCondition:
        conditions = [
            SystemSessionEnvironConditions.by_public_scope(),
            SystemSessionEnvironConditions.by_domain_scope(self.domain_id),
            SystemSessionEnvironConditions.by_project_scope(self.project_id),
        ]

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.or_(*(condition() for condition in conditions))

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()
