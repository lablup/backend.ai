"""Utility functions for repository queries."""

from __future__ import annotations

import sqlalchemy as sa

from .types import QueryCondition


def combine_conditions_or(conditions: list[QueryCondition]) -> QueryCondition:
    """Combine multiple QueryConditions with OR logic.

    Args:
        conditions: List of QueryCondition callables to combine

    Returns:
        A single QueryCondition that applies all conditions with OR logic
    """

    def inner() -> sa.sql.expression.ColumnElement[bool]:
        clauses = [cond() for cond in conditions]
        return sa.or_(*clauses)

    return inner


def negate_conditions(conditions: list[QueryCondition]) -> QueryCondition:
    """Negate multiple QueryConditions with NOT logic.

    Args:
        conditions: List of QueryCondition callables to negate

    Returns:
        A single QueryCondition that negates the AND of all conditions
    """

    def inner() -> sa.sql.expression.ColumnElement[bool]:
        clauses = [cond() for cond in conditions]
        if len(clauses) == 1:
            return sa.not_(clauses[0])
        else:
            return sa.not_(sa.and_(*clauses))

    return inner
