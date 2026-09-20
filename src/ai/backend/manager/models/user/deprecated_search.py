"""User search operations that reach into another entity.

A filter or an order on another entity's column cannot ask whether the caller may
read that row, and a to-many aggregate reruns its subquery for every outer row.
Both are banned by `models/specs/search/AGENTS.md`. What is here shipped before the
rule, is marked deprecated in the schema, and is removed in the next release. Nothing
new goes here; the declarations are in `searchable_fields.py`.
"""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa

from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.project import AssocGroupUserRow, ProjectRow
from ai.backend.manager.models.user.row import UserRow

__all__ = (
    "DeprecatedUserConditions",
    "DeprecatedUserOrders",
)


class DeprecatedUserConditions:
    """Filters on the domain a user belongs to and the projects it is on."""

    @staticmethod
    def exists_domain_combined(domain_conditions: list[QueryCondition]) -> QueryCondition:
        """Every domain condition in one EXISTS, so they match the same domain."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subq = sa.select(sa.literal(1)).where(DomainRow.name == UserRow.domain_name)
            for cond in domain_conditions:
                subq = subq.where(cond())
            return sa.exists(subq)

        return inner

    @staticmethod
    def exists_project_combined(project_conditions: list[QueryCondition]) -> QueryCondition:
        """Every project condition in one EXISTS, so they match the same project."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subq = (
                sa.select(sa.literal(1))
                .select_from(
                    sa.join(
                        AssocGroupUserRow.__table__,
                        ProjectRow.__table__,
                        AssocGroupUserRow.group_id == ProjectRow.id,
                    )
                )
                .where(AssocGroupUserRow.user_id == UserRow.uuid)
            )
            for cond in project_conditions:
                subq = subq.where(cond())
            return sa.exists(subq)

        return inner


class DeprecatedUserOrders:
    """Orders folding the projects a user is on into one value."""

    @staticmethod
    def by_project_name(ascending: bool = True) -> QueryOrder:
        subq: sa.ScalarSelect[Any] = (
            sa.select(sa.func.min(ProjectRow.name))
            .select_from(
                sa.join(
                    AssocGroupUserRow.__table__,
                    ProjectRow.__table__,
                    AssocGroupUserRow.group_id == ProjectRow.id,
                )
            )
            .where(AssocGroupUserRow.user_id == UserRow.uuid)
            .correlate(UserRow)
            .scalar_subquery()
        )
        return subq.asc() if ascending else subq.desc()
