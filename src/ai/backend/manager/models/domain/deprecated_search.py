"""Domain search operations the current rules ban.

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
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.user import UserRow

__all__ = (
    "DeprecatedDomainConditions",
    "DeprecatedDomainOrders",
)


class DeprecatedDomainConditions:
    """Filters on the projects and the users a domain holds."""

    @staticmethod
    def exists_project_combined(project_conditions: list[QueryCondition]) -> QueryCondition:
        """Every project condition in one EXISTS, so they match the same project."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subq = sa.select(sa.literal(1)).where(ProjectRow.domain_name == DomainRow.name)
            for cond in project_conditions:
                subq = subq.where(cond())
            return sa.exists(subq)

        return inner

    @staticmethod
    def exists_user_combined(user_conditions: list[QueryCondition]) -> QueryCondition:
        """Every user condition in one EXISTS, so they match the same user."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subq = sa.select(sa.literal(1)).where(UserRow.domain_name == DomainRow.name)
            for cond in user_conditions:
                subq = subq.where(cond())
            return sa.exists(subq)

        return inner


class DeprecatedDomainOrders:
    """Orders folding the projects or the users a domain holds into one value."""

    @staticmethod
    def _scalar_min(
        column: sa.ColumnElement[Any] | sa.orm.InstrumentedAttribute[Any],
        join_predicate: sa.sql.expression.ColumnElement[bool],
    ) -> sa.ScalarSelect[Any]:
        return (
            sa.select(sa.func.min(column))
            .where(join_predicate)
            .correlate(DomainRow)
            .scalar_subquery()
        )

    @staticmethod
    def by_project_name(ascending: bool = True) -> QueryOrder:
        subq = DeprecatedDomainOrders._scalar_min(
            ProjectRow.name, ProjectRow.domain_name == DomainRow.name
        )
        return subq.asc() if ascending else subq.desc()

    @staticmethod
    def by_user_username(ascending: bool = True) -> QueryOrder:
        subq = DeprecatedDomainOrders._scalar_min(
            UserRow.username, UserRow.domain_name == DomainRow.name
        )
        return subq.asc() if ascending else subq.desc()

    @staticmethod
    def by_user_email(ascending: bool = True) -> QueryOrder:
        subq = DeprecatedDomainOrders._scalar_min(
            UserRow.email, UserRow.domain_name == DomainRow.name
        )
        return subq.asc() if ascending else subq.desc()
