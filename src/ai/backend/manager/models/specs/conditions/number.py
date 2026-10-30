"""Conditions on a column compared as a number."""

from __future__ import annotations

from decimal import Decimal

import sqlalchemy as sa

from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.conditions.types import FilterColumn


class FloatConditions:
    """Floating-point comparisons on one column."""

    _column: FilterColumn

    def __init__(self, column: FilterColumn) -> None:
        self._column = column

    def equals(self, value: float) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._column == value

        return inner

    def not_equals(self, value: float) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._column != value

        return inner

    def greater_than(self, value: float) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._column > value

        return inner

    def greater_than_or_equal(self, value: float) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._column >= value

        return inner

    def less_than(self, value: float) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._column < value

        return inner

    def less_than_or_equal(self, value: float) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._column <= value

        return inner


class DecimalConditions:
    """Decimal comparisons on one column.

    ``DecimalType`` stores the value as VARCHAR, so the column is handed in cast to a
    numeric type; comparing the stored text would order ``"10"`` before ``"9"``.
    """

    _column: FilterColumn

    def __init__(self, column: FilterColumn) -> None:
        self._column = column

    def equals(self, value: Decimal) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._column == value

        return inner

    def not_equals(self, value: Decimal) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._column != value

        return inner

    def greater_than(self, value: Decimal) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._column > value

        return inner

    def greater_than_or_equal(self, value: Decimal) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._column >= value

        return inner

    def less_than(self, value: Decimal) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._column < value

        return inner

    def less_than_or_equal(self, value: Decimal) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._column <= value

        return inner
