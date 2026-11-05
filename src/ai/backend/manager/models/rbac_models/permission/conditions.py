"""Query conditions for role permission rows."""

from __future__ import annotations

import sqlalchemy as sa

from ai.backend.manager.data.permission.types import RoleSource
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role.row import RoleRow

__all__ = ("PermissionConditions",)


class PermissionConditions:
    @staticmethod
    def by_custom_role() -> QueryCondition:
        """The entry belongs to a CUSTOM role. A SYSTEM role's entries follow its role
        preset and are edited there."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return PermissionRow.role_id.in_(
                sa.select(RoleRow.id).where(RoleRow.source == RoleSource.CUSTOM)
            )

        return inner
