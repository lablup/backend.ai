"""Role assignment search operations the current rules ban.

An assignment row joins a user to a role, and a filter on the role it names, or on the
permission entries that role holds, cannot ask whether the caller may read them.
`models/specs/search/AGENTS.md` bans both. What is here shipped before the rule, is
marked deprecated in the schema, and is removed in the next release. Nothing new goes
here; the declarations are in `searchable_fields.py`.
"""

from __future__ import annotations

import sqlalchemy as sa

from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow

__all__ = ("DeprecatedRoleAssignmentConditions",)


class DeprecatedRoleAssignmentConditions:
    """Filters on the role an assignment names and on the permissions that role holds."""

    @staticmethod
    def exists_role_combined(role_conditions: list[QueryCondition]) -> QueryCondition:
        """Every condition in one EXISTS, so they match the same role."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(sa.literal(1))
                .where(RoleRow.id == UserRoleRow.role_id)
                .correlate(UserRoleRow)
            )
            for condition in role_conditions:
                subquery = subquery.where(condition())
            return sa.exists(subquery)

        return inner

    @staticmethod
    def exists_permission_combined(permission_conditions: list[QueryCondition]) -> QueryCondition:
        """Every condition in one EXISTS, so they match the same permission entry."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(sa.literal(1))
                .where(PermissionRow.role_id == UserRoleRow.role_id)
                .correlate(UserRoleRow)
            )
            for condition in permission_conditions:
                subquery = subquery.where(condition())
            return sa.exists(subquery)

        return inner
