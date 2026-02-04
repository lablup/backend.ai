"""Query conditions and orders for domain repository operations."""

from __future__ import annotations

import sqlalchemy as sa

from ai.backend.manager.api.gql.base import StringMatchSpec
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder

__all__ = (
    "DomainConditions",
    "DomainOrders",
)


class DomainConditions:
    """Query conditions for filtering domains."""

    # ==================== Name Filters ====================

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DomainRow.name.ilike(f"%{spec.value}%")
            else:
                condition = DomainRow.name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(DomainRow.name) == spec.value.lower()
            else:
                condition = DomainRow.name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DomainRow.name.ilike(f"{spec.value}%")
            else:
                condition = DomainRow.name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DomainRow.name.ilike(f"%{spec.value}")
            else:
                condition = DomainRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    # ==================== Active Status Filters ====================

    @staticmethod
    def by_is_active(is_active: bool) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainRow.is_active == is_active

        return inner

    # ==================== Integration ID Filters ====================

    @staticmethod
    def by_integration_id_equals(integration_id: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainRow.integration_id == integration_id

        return inner

    @staticmethod
    def by_has_integration_id(has_integration: bool) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if has_integration:
                return DomainRow.integration_id.is_not(None)
            return DomainRow.integration_id.is_(None)

        return inner

    # ==================== Cursor Pagination ====================

    @staticmethod
    def by_cursor_forward(cursor_name: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(DomainRow.created_at)
                .where(DomainRow.name == cursor_name)
                .scalar_subquery()
            )
            return DomainRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_name: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(DomainRow.created_at)
                .where(DomainRow.name == cursor_name)
                .scalar_subquery()
            )
            return DomainRow.created_at > subquery

        return inner


class DomainOrders:
    """Query orders for sorting domains."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return DomainRow.name.asc()
        return DomainRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return DomainRow.created_at.asc()
        return DomainRow.created_at.desc()

    @staticmethod
    def modified_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return DomainRow.modified_at.asc()
        return DomainRow.modified_at.desc()

    @staticmethod
    def is_active(ascending: bool = True) -> QueryOrder:
        if ascending:
            return DomainRow.is_active.asc()
        return DomainRow.is_active.desc()
