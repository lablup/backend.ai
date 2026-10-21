from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.filter_specs import UUIDEqualMatchSpec
from ai.backend.common.data.system_session_environ.types import SystemSessionEnvironScopeType
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope
from ai.backend.manager.models.system_session_environ.searchable_fields import (
    SystemSessionEnvironSearchableFields,
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
        fields = SystemSessionEnvironSearchableFields.own

        def at(
            scope_type: SystemSessionEnvironScopeType, scope_id: UUID
        ) -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                fields.scope_type.filter.equals(scope_type)(),
                fields.scope_id.filter.equals(UUIDEqualMatchSpec(value=scope_id, negated=False))(),
            )

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.or_(
                at(SystemSessionEnvironScopeType.PUBLIC, global_entity_id(GlobalEntityName.PUBLIC)),
                at(SystemSessionEnvironScopeType.DOMAIN, self.domain_id),
                at(SystemSessionEnvironScopeType.PROJECT, self.project_id),
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()
