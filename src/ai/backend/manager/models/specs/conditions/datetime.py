"""Datetime conditions on one column."""

from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa

from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.conditions.types import FilterColumn


class DateTimeConditions:
    """Datetime comparisons on one column, bounds exclusive; a ``None`` value gives none."""

    _column: FilterColumn

    def __init__(self, column: FilterColumn) -> None:
        self._column = column

    def equals(self, value: datetime | None) -> QueryCondition | None:
        if value is None:
            return None

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._column == value

        return inner

    def before(self, value: datetime | None) -> QueryCondition | None:
        if value is None:
            return None

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._column < value

        return inner

    def after(self, value: datetime | None) -> QueryCondition | None:
        if value is None:
            return None

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._column > value

        return inner
