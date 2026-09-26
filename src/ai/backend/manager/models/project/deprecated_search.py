"""Project search operations the current rules ban.

A filter or an order on another entity's column cannot ask whether the caller may
read that row, and a to-many aggregate reruns its subquery for every outer row.
Both are banned by `models/specs/search/AGENTS.md`. What is here shipped before the
rule, is marked deprecated in the schema, and is removed in the next release. Nothing
new goes here; the declarations are in `searchable_fields.py`.
"""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa

from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.virtual_entity.queries import user_scope_membership_exists

__all__ = (
    "DeprecatedProjectConditions",
    "DeprecatedProjectOrders",
)


class DeprecatedProjectConditions:
    """Filters on the domain a project belongs to and the users enrolled in it."""

    @staticmethod
    def exists_domain_combined(domain_conditions: list[QueryCondition]) -> QueryCondition:
        """Every domain condition in one EXISTS, so they match the same domain."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subq = sa.select(sa.literal(1)).where(DomainRow.name == ProjectRow.domain_name)
            for cond in domain_conditions:
                subq = subq.where(cond())
            return sa.exists(subq)

        return inner

    @staticmethod
    def exists_user_combined(user_conditions: list[QueryCondition]) -> QueryCondition:
        """Every user condition in one EXISTS, so they match the same enrolled user."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subq = (
                sa.select(sa.literal(1))
                .select_from(UserRow)
                .where(
                    user_scope_membership_exists(
                        ProjectEntityType(), ProjectRow.id, UserRow.uuid
                    ).correlate(ProjectRow, UserRow)
                )
            )
            for cond in user_conditions:
                subq = subq.where(cond())
            return sa.exists(subq)

        return inner


class DeprecatedProjectOrders:
    """Orders folding the users a project holds into one value."""

    @staticmethod
    def _scalar_user_min(
        column: sa.ColumnElement[Any] | sa.orm.InstrumentedAttribute[Any],
    ) -> sa.ScalarSelect[Any]:
        return (
            sa.select(sa.func.min(column))
            .select_from(UserRow)
            .where(
                user_scope_membership_exists(
                    ProjectEntityType(), ProjectRow.id, UserRow.uuid
                ).correlate(ProjectRow, UserRow)
            )
            .correlate(ProjectRow)
            .scalar_subquery()
        )

    @staticmethod
    def by_user_username(ascending: bool = True) -> QueryOrder:
        subq = DeprecatedProjectOrders._scalar_user_min(UserRow.username)
        return subq.asc() if ascending else subq.desc()

    @staticmethod
    def by_user_email(ascending: bool = True) -> QueryOrder:
        subq = DeprecatedProjectOrders._scalar_user_min(UserRow.email)
        return subq.asc() if ascending else subq.desc()
