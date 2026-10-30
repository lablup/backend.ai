"""Containment conditions on one array column."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.conditions.types import FilterColumn


class ArrayConditions[V]:
    """Containment of values in one array column.

    ``element_type`` is the array's element type, which the compared literal is cast to.
    """

    _column: FilterColumn
    _element_type: sa.types.TypeEngine[V]

    def __init__(self, column: FilterColumn, element_type: sa.types.TypeEngine[V]) -> None:
        self._column = column
        self._element_type = element_type

    def contains(self, value: V) -> QueryCondition:
        return self.contains_all([value])

    def contains_all(self, values: Sequence[V]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._column.bool_op("@>")(self._literal(values))

        return inner

    def contains_any(self, values: Sequence[V]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._column.bool_op("&&")(self._literal(values))

        return inner

    def _literal(self, values: Sequence[V]) -> sa.sql.expression.ColumnElement[Any]:
        return sa.cast(list(values), postgresql.ARRAY(self._element_type))
