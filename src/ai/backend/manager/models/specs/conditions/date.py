"""Date conditions on one column."""

from __future__ import annotations

from datetime import date

import sqlalchemy as sa

from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.conditions.types import FilterColumn


class DateConditions:
    """Date comparisons on one column.

    ``before`` and ``after`` are exclusive; ``on_or_before`` and ``on_or_after`` are the
    inclusive pair a date range asks for.
    """

    _column: FilterColumn

    def __init__(self, column: FilterColumn) -> None:
        self._column = column

    def equals(self, value: date) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._column == value

        return inner

    def not_equals(self, value: date) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._column != value

        return inner

    def before(self, value: date) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._column < value

        return inner

    def after(self, value: date) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._column > value

        return inner

    def on_or_before(self, value: date) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._column <= value

        return inner

    def on_or_after(self, value: date) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._column >= value

        return inner
