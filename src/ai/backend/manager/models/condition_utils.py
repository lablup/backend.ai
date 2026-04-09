"""Shared utilities for building query conditions across entity domains."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import StringInMatchSpec
from ai.backend.manager.repositories.base import QueryCondition


def make_string_in_factory(
    column: sa.orm.InstrumentedAttribute[Any],
) -> Callable[[StringInMatchSpec], QueryCondition]:
    """Create a factory for string ``IN`` conditions on the given column.

    The returned factory accepts a ``StringInMatchSpec`` (honoring
    ``case_insensitive`` and ``negated``) and returns a ``QueryCondition``.

    Usage in entity-specific Conditions class::

        class MyConditions:
            by_name_in = staticmethod(make_string_in_factory(MyRow.name))

    Then in the adapter::

        self.convert_string_filter(
            filter_req.name,
            contains_factory=MyConditions.by_name_contains,
            equals_factory=MyConditions.by_name_equals,
            starts_with_factory=MyConditions.by_name_starts_with,
            ends_with_factory=MyConditions.by_name_ends_with,
            in_factory=MyConditions.by_name_in,
        )
    """

    def factory(spec: StringInMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(column).in_([v.lower() for v in spec.values])
            else:
                condition = column.in_(spec.values)
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    return factory


def make_nested_string_in_factory(
    column: sa.orm.InstrumentedAttribute[Any],
    exists_wrapper: Callable[
        [sa.sql.expression.ColumnElement[bool]], sa.sql.expression.ColumnElement[bool]
    ],
) -> Callable[[StringInMatchSpec], QueryCondition]:
    """Create a factory for string ``IN`` conditions wrapped in an EXISTS subquery.

    Same semantics as ``make_string_in_factory`` but wraps the produced
    ``IN`` predicate inside the supplied ``exists_wrapper`` so that the
    resulting condition matches rows whose related entity satisfies the
    column predicate.

    Usage::

        class DomainConditions:
            by_user_username_in = staticmethod(
                make_nested_string_in_factory(
                    UserRow.username,
                    lambda c: DomainConditions._exists_user(c),
                )
            )
    """

    def factory(spec: StringInMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(column).in_([v.lower() for v in spec.values])
            else:
                condition = column.in_(spec.values)
            if spec.negated:
                condition = sa.not_(condition)
            return exists_wrapper(condition)

        return inner

    return factory


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
