"""Role search operations the current rules ban.

A filter reaching a relation row cannot ask whether the caller may read the entity on
its other side, which `models/specs/search/AGENTS.md` bans; the users holding a role
are read through `HeldRoleTarget` instead. What is here shipped before the rule, is
marked deprecated in the schema, and is removed in the next release. Nothing new goes
here; the declarations are in `searchable_fields.py`.
"""

from __future__ import annotations

import sqlalchemy as sa

from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow

__all__ = ("DeprecatedRoleConditions",)


class DeprecatedRoleConditions:
    """Filters on the assignment rows a role holds."""

    @staticmethod
    def exists_assignment_combined(assignment_conditions: list[QueryCondition]) -> QueryCondition:
        """Every condition in one EXISTS, so they match the same assignment row."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(sa.literal(1)).where(UserRoleRow.role_id == RoleRow.id).correlate(RoleRow)
            )
            for condition in assignment_conditions:
                subquery = subquery.where(condition())
            return sa.exists(subquery)

        return inner
