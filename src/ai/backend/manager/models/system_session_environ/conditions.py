from __future__ import annotations

import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.system_session_environ.types import SystemSessionEnvironScopeType
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.system_session_environ.row import SystemSessionEnvironRow

__all__ = ("SystemSessionEnvironConditions",)


class SystemSessionEnvironConditions:
    @staticmethod
    def by_public_scope() -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                SystemSessionEnvironRow.scope_type == SystemSessionEnvironScopeType.PUBLIC,
                SystemSessionEnvironRow.scope_id == global_entity_id(GlobalEntityName.PUBLIC),
            )

        return inner

    @staticmethod
    def by_domain_scope(domain_id: DomainID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                SystemSessionEnvironRow.scope_type == SystemSessionEnvironScopeType.DOMAIN,
                SystemSessionEnvironRow.scope_id == domain_id,
            )

        return inner

    @staticmethod
    def by_project_scope(project_id: ProjectID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                SystemSessionEnvironRow.scope_type == SystemSessionEnvironScopeType.PROJECT,
                SystemSessionEnvironRow.scope_id == project_id,
            )

        return inner
