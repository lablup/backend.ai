"""Order by one column or scalar expression."""

from __future__ import annotations

from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.manager.models.clauses import QueryOrder
from ai.backend.manager.models.specs.orders.base import SearchOrder


class ColumnOrder(SearchOrder):
    """Orders by a column, or by a correlated scalar subquery reading a related row."""

    _expression: InstrumentedAttribute[Any] | sa.sql.expression.ColumnElement[Any]

    def __init__(
        self, expression: InstrumentedAttribute[Any] | sa.sql.expression.ColumnElement[Any]
    ) -> None:
        self._expression = expression

    @override
    def apply(self, ascending: bool) -> QueryOrder:
        if ascending:
            return self._expression.asc()
        return self._expression.desc()
