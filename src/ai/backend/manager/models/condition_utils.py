"""Shared utilities for building query conditions across entity domains."""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa

from ai.backend.manager.repositories.base import QueryCondition


def make_int_conditions(
    column: sa.orm.InstrumentedAttribute[Any],
) -> type:
    """Generate a class with int comparison condition factories for a column.

    Returns a class with ``equals``, ``not_equals``, ``gt``, ``gte``, ``lt``, ``lte``
    static methods, each returning a ``QueryCondition``.

    Usage in entity-specific Conditions class::

        class MyConditions:
            by_some_int_field = make_int_conditions(MyRow.some_int_field)

    Then in the adapter::

        condition = int_filter.build_query_condition(
            equals_factory=MyConditions.by_some_int_field.equals,
            not_equals_factory=MyConditions.by_some_int_field.not_equals,
            greater_than_factory=MyConditions.by_some_int_field.gt,
            greater_than_or_equal_factory=MyConditions.by_some_int_field.gte,
            less_than_factory=MyConditions.by_some_int_field.lt,
            less_than_or_equal_factory=MyConditions.by_some_int_field.lte,
        )
    """

    class _IntConditions:
        @staticmethod
        def equals(val: int) -> QueryCondition:
            def inner() -> sa.sql.expression.ColumnElement[bool]:
                return column == val

            return inner

        @staticmethod
        def not_equals(val: int) -> QueryCondition:
            def inner() -> sa.sql.expression.ColumnElement[bool]:
                return column != val

            return inner

        @staticmethod
        def gt(val: int) -> QueryCondition:
            def inner() -> sa.sql.expression.ColumnElement[bool]:
                return column > val

            return inner

        @staticmethod
        def gte(val: int) -> QueryCondition:
            def inner() -> sa.sql.expression.ColumnElement[bool]:
                return column >= val

            return inner

        @staticmethod
        def lt(val: int) -> QueryCondition:
            def inner() -> sa.sql.expression.ColumnElement[bool]:
                return column < val

            return inner

        @staticmethod
        def lte(val: int) -> QueryCondition:
            def inner() -> sa.sql.expression.ColumnElement[bool]:
                return column <= val

            return inner

    return _IntConditions
