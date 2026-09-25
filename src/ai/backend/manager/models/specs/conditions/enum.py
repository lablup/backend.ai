"""Enum conditions on one column."""

from __future__ import annotations

from collections.abc import Collection
from enum import Enum

import sqlalchemy as sa

from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.conditions.types import FilterColumn


class EnumConditions[E: Enum]:
    """Enum equality and membership on one column."""

    _column: FilterColumn
    _enum_type: type[E]

    def __init__(self, column: FilterColumn, enum_type: type[E]) -> None:
        self._column = column
        self._enum_type = enum_type

    def to_value(self, value: object) -> E:
        """Look ``value`` up in the column's enum, e.g. a request-side member of the same value."""
        return self._enum_type(value)

    def equals(self, value: E) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._column == value

        return inner

    def not_equals(self, value: E) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._column != value

        return inner

    def in_(self, values: Collection[E]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._column.in_(values)

        return inner

    def not_in(self, values: Collection[E]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._column.not_in(values)

        return inner
