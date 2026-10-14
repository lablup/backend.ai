from __future__ import annotations

from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.system_session_environ.types import SystemSessionEnvironScopeType
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.system_session_environ.row import SystemSessionEnvironRow

__all__ = ("SystemSessionEnvironConditions",)


class SystemSessionEnvironConditions:
    @staticmethod
    def at_global_or_scopes(
        domain_ids: Collection[DomainID],
        project_ids: Collection[ProjectID],
    ) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.or_(
                SystemSessionEnvironRow.scope_type == SystemSessionEnvironScopeType.GLOBAL,
                sa.and_(
                    SystemSessionEnvironRow.scope_type == SystemSessionEnvironScopeType.DOMAIN,
                    SystemSessionEnvironRow.scope_id.in_(domain_ids),
                ),
                sa.and_(
                    SystemSessionEnvironRow.scope_type == SystemSessionEnvironScopeType.PROJECT,
                    SystemSessionEnvironRow.scope_id.in_(project_ids),
                ),
            )

        return inner
