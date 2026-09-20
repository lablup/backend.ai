"""Project search operations the current rules ban.

A to-many aggregate reruns its subquery for every outer row, so folding the users a
project holds with `MIN` is banned by `models/specs/search/AGENTS.md`. What is here
shipped before the rule, is marked deprecated in the schema, and is removed in the
next release. Nothing new goes here; the declarations are in `searchable_fields.py`.
"""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa

from ai.backend.manager.models.clauses import QueryOrder
from ai.backend.manager.models.project.row import AssocGroupUserRow, ProjectRow
from ai.backend.manager.models.user import UserRow

__all__ = ("DeprecatedProjectOrders",)


class DeprecatedProjectOrders:
    """Orders folding the users a project holds into one value."""

    @staticmethod
    def _scalar_user_min(
        column: sa.ColumnElement[Any] | sa.orm.InstrumentedAttribute[Any],
    ) -> sa.ScalarSelect[Any]:
        return (
            sa.select(sa.func.min(column))
            .select_from(
                sa.join(
                    AssocGroupUserRow.__table__,
                    UserRow.__table__,
                    AssocGroupUserRow.user_id == UserRow.uuid,
                )
            )
            .where(AssocGroupUserRow.group_id == ProjectRow.id)
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
