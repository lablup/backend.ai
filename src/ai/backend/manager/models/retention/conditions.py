"""Query conditions for retention policy rows."""

from __future__ import annotations

import uuid
from collections.abc import Collection
from uuid import UUID

import sqlalchemy as sa

from ai.backend.manager.data.retention.types import RetentionCategory
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.retention.row import RetentionPolicyRow

__all__ = ("RetentionPolicyConditions",)


class RetentionPolicyConditions:
    @staticmethod
    def by_ids(ids: Collection[UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RetentionPolicyRow.id.in_(ids)

        return inner

    @staticmethod
    def by_category_equals(category: RetentionCategory) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RetentionPolicyRow.category == category

        return inner

    @staticmethod
    def by_category_in(categories: Collection[RetentionCategory]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RetentionPolicyRow.category.in_(categories)

        return inner

    @staticmethod
    def by_enabled(enabled: bool) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RetentionPolicyRow.enabled.is_(enabled)

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor).

        Reads the cursor row's ``category`` and compares against that, because ``category`` is what
        the page is ordered by — comparing ids would draw the page boundary on a column the
        result is not sorted by.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(RetentionPolicyRow.category)
                .where(RetentionPolicyRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return RetentionPolicyRow.category > subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor).

        Reads the cursor row's ``category`` and compares against that, because ``category`` is what
        the page is ordered by — comparing ids would draw the page boundary on a column the
        result is not sorted by.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(RetentionPolicyRow.category)
                .where(RetentionPolicyRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return RetentionPolicyRow.category < subquery

        return inner
