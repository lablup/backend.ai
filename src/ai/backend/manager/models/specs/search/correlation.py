"""How an entity reaches the rows of another table its fields live in."""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa

from ai.backend.manager.errors.repository import EmptyMatchConditionError
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.conditions.types import FilterColumn
from ai.backend.manager.models.specs.orders.column import ColumnOrder

type CorrelationSource = type[Any] | sa.sql.expression.FromClause


class _Correlation:
    """The join through which an entity reaches another table's rows.

    Holds what both shapes need: the joined rows, the outer row they correlate to, and
    the EXISTS subquery built from the two.
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

    def _require_conditions(self, conditions: list[QueryCondition], mode: str) -> None:
        if not conditions:
            raise EmptyMatchConditionError(
                extra_msg=f"`{mode}` was given no condition; `exists` asks for a related row"
            )

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


class ToManyCorrelation(_Correlation):
    """Rows of ``child_row`` joined to the outer ``correlate_row`` by ``join_predicate``.

    Each matching mode takes the conditions one child row has to meet, so they land on
    the same row, and refuses an empty list: whether a child exists at all is what
    ``exists`` and ``not_exists`` answer.
    """

    def exists(self) -> QueryCondition:
        """The outer row has at least one child row."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._exists([])

        return inner

    def not_exists(self) -> QueryCondition:
        """The outer row has no child row."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.not_(self._exists([]))

        return inner

    def some(self, conditions: list[QueryCondition]) -> QueryCondition:
        self._require_conditions(conditions, "some")

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._exists(conditions)

        return inner

    def every(self, conditions: list[QueryCondition]) -> QueryCondition:
        """True for an outer row with no child row."""
        self._require_conditions(conditions, "every")

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            failing = sa.not_(sa.and_(*[condition() for condition in conditions]))
            return sa.not_(self._exists([lambda: failing]))

        return inner

    def none(self, conditions: list[QueryCondition]) -> QueryCondition:
        self._require_conditions(conditions, "none")

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.not_(self._exists(conditions))

        return inner


class ToOneCorrelation(_Correlation):
    """The single row of ``child_row`` the outer ``correlate_row`` points at."""

    def exists(self) -> QueryCondition:
        """The related row exists, whatever it holds."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._exists([])

        return inner

    def has(self, conditions: list[QueryCondition]) -> QueryCondition:
        """The related row exists and meets every condition."""
        self._require_conditions(conditions, "has")

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._exists(conditions)

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
