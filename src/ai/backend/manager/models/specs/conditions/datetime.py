"""Datetime conditions on one column."""

from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa

from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.conditions.types import FilterColumn


class DateTimeConditions:
    """Datetime comparisons on one column; both bounds are exclusive."""

    _column: FilterColumn

    def __init__(self, column: FilterColumn) -> None:
        self._column = column

    def equals(self, value: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._column == value

        return inner

    def before(self, value: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._column < value

        return inner

    def after(self, value: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._column > value

        return inner

    def is_null(self) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._column.is_(None)

        return inner

    def is_not_null(self) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._column.isnot(None)

        return inner
