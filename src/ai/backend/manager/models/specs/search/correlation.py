"""How an entity reaches the rows of another table its fields live in."""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa

from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.conditions.types import FilterColumn
from ai.backend.manager.models.specs.orders.column import ColumnOrder

type CorrelationSource = type[Any] | sa.sql.expression.FromClause


class ToManyCorrelation:
    """Rows of ``child_row`` joined to the outer ``correlate_row`` by ``join_predicate``.

    Each quantifier takes the conditions one child row has to meet, so they land on the
    same row.
    """

    _child_row: CorrelationSource
    _correlate_row: CorrelationSource
    _join_predicate: sa.sql.expression.ColumnElement[bool]

    def __init__(
        self,
        child_row: CorrelationSource,
        correlate_row: CorrelationSource,
        join_predicate: sa.sql.expression.ColumnElement[bool],
    ) -> None:
        self._child_row = child_row
        self._correlate_row = correlate_row
        self._join_predicate = join_predicate

    def some(self, conditions: list[QueryCondition]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._exists(conditions)

        return inner

    def every(self, conditions: list[QueryCondition]) -> QueryCondition:
        """True for an outer row with no child row."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            clauses = [condition() for condition in conditions]
            failing = sa.not_(clauses[0]) if len(clauses) == 1 else sa.not_(sa.and_(*clauses))
            return sa.not_(self._exists([lambda: failing]))

        return inner

    def none(self, conditions: list[QueryCondition]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.not_(self._exists(conditions))

        return inner

    def _exists(self, conditions: list[QueryCondition]) -> sa.sql.expression.ColumnElement[bool]:
        subquery = (
            sa.select(sa.literal(1))
            .select_from(self._child_row)
            .where(self._join_predicate)
            .correlate(self._correlate_row)
        )
        for condition in conditions:
            subquery = subquery.where(condition())
        return sa.exists(subquery)


class ToOneCorrelation:
    """The single row of ``child_row`` the outer ``correlate_row`` points at."""

    _child_row: CorrelationSource
    _correlate_row: CorrelationSource
    _join_predicate: sa.sql.expression.ColumnElement[bool]

    def __init__(
        self,
        child_row: CorrelationSource,
        correlate_row: CorrelationSource,
        join_predicate: sa.sql.expression.ColumnElement[bool],
    ) -> None:
        self._child_row = child_row
        self._correlate_row = correlate_row
        self._join_predicate = join_predicate

    def has(self, conditions: list[QueryCondition]) -> QueryCondition:
        """The related row exists and meets every condition."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(sa.literal(1))
                .select_from(self._child_row)
                .where(self._join_predicate)
                .correlate(self._correlate_row)
            )
            for condition in conditions:
                subquery = subquery.where(condition())
            return sa.exists(subquery)

        return inner

    def order(self, child_column: FilterColumn) -> ColumnOrder:
        """Order the outer rows by a column of the related row."""
        value = (
            sa.select(child_column)
            .where(self._join_predicate)
            .correlate(self._correlate_row)
            .scalar_subquery()
        )
        return ColumnOrder(value)
