"""Boolean conditions on one column."""

from __future__ import annotations

import sqlalchemy as sa

from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.conditions.types import FilterColumn


class BoolConditions:
    """Boolean equality on one column; a ``None`` value gives no condition."""

    _column: FilterColumn

    def __init__(self, column: FilterColumn) -> None:
        self._column = column

    def equals(self, value: bool | None) -> QueryCondition | None:
        if value is None:
            return None

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._column == value

        return inner
