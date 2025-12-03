"""Base types and utilities for repository layer."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Generic, TypeVar

import sqlalchemy as sa
from sqlalchemy.engine import Row

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession as SASession

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

    @abstractmethod
    def compute_page_info(self, rows: list[Row], total_count: int) -> _PageInfoResult[Row]:
        """Compute pagination info and slice rows if needed.

        Args:
            rows: The rows returned from query (may include extra row for page detection)
            total_count: Total count of items matching the query

        Returns:
            _PageInfoResult containing sliced rows and pagination flags
        """

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

    def compute_page_info(self, rows: list[Row], total_count: int) -> _PageInfoResult[Row]:
        """Compute pagination info for offset-based pagination."""

        has_previous_page = self.offset > 0
        has_next_page = (self.offset + len(rows)) < total_count
        return _PageInfoResult(
            rows=rows,
            has_next_page=has_next_page,
            has_previous_page=has_previous_page,
        )


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
        This applies LIMIT + 1 for has_next_page detection.
        """

        return query.limit(self.first + 1)

    def compute_page_info(self, rows: list[Row], total_count: int) -> _PageInfoResult[Row]:
        """Compute pagination info for cursor-based forward pagination."""

        has_previous_page = True  # after cursor exists means previous page exists
        has_next_page = len(rows) > self.first
        if has_next_page:
            rows = rows[: self.first]
        return _PageInfoResult(
            rows=rows,
            has_next_page=has_next_page,
            has_previous_page=has_previous_page,
        )


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
        This applies LIMIT + 1 for has_previous_page detection and may require result reversal.
        """

        return query.limit(self.last + 1)

    def compute_page_info(self, rows: list[Row], total_count: int) -> _PageInfoResult[Row]:
        """Compute pagination info for cursor-based backward pagination."""

        has_next_page = True  # before cursor exists means next page exists
        has_previous_page = len(rows) > self.last
        if has_previous_page:
            rows = rows[: self.last]
        return _PageInfoResult(
            rows=rows,
            has_next_page=has_next_page,
            has_previous_page=has_previous_page,
        )


@dataclass
class Querier:
    """Bundles query conditions, orders, and pagination for repository queries."""

    pagination: QueryPagination
    conditions: list[QueryCondition] = field(default_factory=list)
    orders: list[QueryOrder] = field(default_factory=list)


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


def _apply_querier(
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
    query = querier.pagination.apply(query)

    return query


TRow = TypeVar("TRow", bound=Row)


@dataclass
class _PageInfoResult(Generic[TRow]):
    """Result of compute_page_info containing sliced rows and pagination flags."""

    rows: list[TRow]
    has_next_page: bool
    has_previous_page: bool


@dataclass
class QuerierResult(Generic[TRow]):
    """Result of executing a query with querier."""

    rows: list[TRow]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


async def execute_querier(
    db_sess: SASession,
    query: sa.sql.Select,
    querier: Querier,
) -> QuerierResult[Row]:
    """Execute query with querier and return rows with total_count and pagination info.

    Uses count().over() window function for efficient counting in most cases.
    Falls back to separate count query only when rows is empty (offset exceeds total).

    For cursor-based pagination, fetches N+1 rows to detect has_next_page/has_previous_page,
    then slices to return only the requested count.

    Args:
        db_sess: Database session
        query: SELECT query with count().over().label("total_count") included
        querier: Querier for filtering, ordering, and pagination

    Returns:
        QuerierResult containing rows, total_count, and pagination info
    """
    initial_query = query
    query = _apply_querier(query, querier)

    result = await db_sess.execute(query)
    rows = list(result.all())

    total_count: int
    if rows:
        total_count = rows[0].total_count
    else:
        # Fallback: Get total_count from window function without pagination
        # Re-execute query with conditions but without pagination
        fallback_query = initial_query
        for condition in querier.conditions:
            fallback_query = fallback_query.where(condition())

        result = await db_sess.execute(fallback_query)
        first_row = result.first()
        total_count = first_row.total_count if first_row else 0

    # Calculate pagination info
    page_info = querier.pagination.compute_page_info(rows, total_count)

    return QuerierResult(
        rows=page_info.rows,
        total_count=total_count,
        has_next_page=page_info.has_next_page,
        has_previous_page=page_info.has_previous_page,
    )
