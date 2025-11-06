"""Base types and utilities for repository layer."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Optional

import sqlalchemy as sa

# QueryCondition now returns a ColumnElement (whereclause) instead of modifying stmt
type QueryCondition = Callable[[], sa.sql.expression.ColumnElement[bool]]

type QueryOrder = sa.sql.ClauseElement


class QueryPagination(ABC):
    """
    Base class for pagination strategies.

    Subclasses must implement the apply() method to transform a SQLAlchemy
    select statement with appropriate pagination logic.
    """

    @abstractmethod
    def apply(self, query: sa.sql.Select) -> sa.sql.Select:
        """Apply pagination to a SQLAlchemy select statement."""

        raise NotImplementedError


@dataclass
class OffsetPagination(QueryPagination):
    """
    Offset-based pagination using limit and offset.

    This is the traditional SQL pagination approach where you specify:
    - limit: Maximum number of items to return
    - offset: Number of items to skip from the beginning
    """

    limit: int
    """Maximum number of items to return (must be positive)."""

    offset: int = 0
    """Number of items to skip from the beginning (must be non-negative)."""

    def apply(self, query: sa.sql.Select) -> sa.sql.Select:
        """Apply offset-based pagination to query."""

        query = query.limit(self.limit)
        if self.offset > 0:
            query = query.offset(self.offset)
        return query


@dataclass
class CursorForwardPagination(QueryPagination):
    """
    Cursor-based forward pagination using first and after.

    This follows the GraphQL Relay Cursor Connections specification for forward pagination.
    Use this to paginate forward through a result set:
    - first: Number of items to return from the cursor position
    - after: Cursor representing the position to start after
    """

    first: int
    """Number of items to return (must be positive)."""

    after: str
    """
    Base64-encoded cursor representing the position to start after.

    The cursor encodes the values of the ordering columns for a specific item.
    Results will start after this cursor position based on the query ordering.
    """

    def apply(self, query: sa.sql.Select) -> sa.sql.Select:
        """
        Apply cursor-based forward pagination to query.

        Note: Cursor decoding and WHERE clause for cursor position
        should be handled by the caller before building the query.
        This only applies the LIMIT.
        """

        return query.limit(self.first)


@dataclass
class CursorBackwardPagination(QueryPagination):
    """
    Cursor-based backward pagination using last and before.

    This follows the GraphQL Relay Cursor Connections specification for backward pagination.
    Use this to paginate backward through a result set:
    - last: Number of items to return before the cursor position
    - before: Cursor representing the position to end before
    """

    last: int
    """Number of items to return (must be positive)."""

    before: str
    """
    Base64-encoded cursor representing the position to end before.

    The cursor encodes the values of the ordering columns for a specific item.
    Results will end before this cursor position based on the query ordering.
    """

    def apply(self, query: sa.sql.Select) -> sa.sql.Select:
        """
        Apply cursor-based backward pagination to query.

        Note: Cursor decoding and WHERE clause for cursor position
        should be handled by the caller before building the query.
        This only applies the LIMIT and may require result reversal.
        """

        return query.limit(self.last)


@dataclass
class Querier:
    """Bundles query conditions, orders, and pagination for repository queries."""

    conditions: list[QueryCondition] = field(default_factory=list)
    orders: list[QueryOrder] = field(default_factory=list)
    pagination: Optional[QueryPagination] = None


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


def apply_querier(
    query: sa.sql.Select,
    querier: Querier,
) -> sa.sql.Select:
    """Apply query conditions, orders, and pagination to a SQLAlchemy select statement.

    Args:
        query: The base SELECT statement
        querier: Querier containing conditions, orders, and pagination to apply

    Returns:
        The modified SELECT statement with conditions, orders, and pagination applied
    """
    # Apply all conditions
    for condition in querier.conditions:
        query = query.where(condition())

    # Apply all orders
    for order in querier.orders:
        query = query.order_by(order)

    # Apply pagination
    if querier.pagination is not None:
        query = querier.pagination.apply(query)

    return query
