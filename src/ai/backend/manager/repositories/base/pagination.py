"""Pagination strategies for repository queries."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, Optional

import sqlalchemy as sa

from .types import QueryCondition, QueryOrder, TRow

if TYPE_CHECKING:
    from sqlalchemy.engine import Row


class QueryPagination(ABC):
    """
    Base class for pagination strategies.

    Subclasses must implement the apply() method to transform a SQLAlchemy
    select statement with appropriate pagination logic.
    """

    @property
    @abstractmethod
    def uses_window_function(self) -> bool:
        """Whether this pagination uses window function for total_count.

        Returns:
            True if window function should be added to main query (Offset),
            False if separate count query should be used (Cursor).
        """
        raise NotImplementedError

    @abstractmethod
    def apply(self, query: sa.sql.Select) -> sa.sql.Select:
        """Apply pagination to a SQLAlchemy select statement."""

        raise NotImplementedError

    @abstractmethod
    def compute_page_info(self, rows: list[Row], total_count: int) -> PageInfoResult[Row]:
        """Compute pagination info and slice rows if needed.

        Args:
            rows: The rows returned from query (may include extra row for page detection)
            total_count: Total count of items matching the query

        Returns:
            _PageInfoResult containing sliced rows and pagination flags
        """

        raise NotImplementedError


@dataclass
class PageInfoResult(Generic[TRow]):
    """Result of compute_page_info containing sliced rows and pagination flags."""

    rows: list[TRow]
    has_next_page: bool
    has_previous_page: bool


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

    @property
    def uses_window_function(self) -> bool:
        return True

    def apply(self, query: sa.sql.Select) -> sa.sql.Select:
        """Apply offset-based pagination to query."""

        query = query.limit(self.limit)
        if self.offset > 0:
            query = query.offset(self.offset)
        return query

    def compute_page_info(self, rows: list[Row], total_count: int) -> PageInfoResult[Row]:
        """Compute pagination info for offset-based pagination."""

        has_previous_page = self.offset > 0
        has_next_page = (self.offset + len(rows)) < total_count
        return PageInfoResult(
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
    - cursor_condition: Optional QueryCondition for WHERE clause (e.g., id > cursor_id).
      If None, starts from the beginning.
    - cursor_order: QueryOrder for cursor-based ordering (e.g., created_at ASC)
    """

    first: int
    """Number of items to return (must be positive)."""

    cursor_order: QueryOrder
    """Ordering for cursor-based pagination (e.g., ORDER BY created_at ASC)."""

    cursor_condition: Optional[QueryCondition] = None
    """Optional QueryCondition for cursor position. If None, starts from the beginning."""

    @property
    def uses_window_function(self) -> bool:
        return False

    def apply(self, query: sa.sql.Select) -> sa.sql.Select:
        """
        Apply cursor-based forward pagination to query.

        Applies cursor condition (if present), cursor order, and LIMIT + 1 for has_next_page detection.
        """
        if self.cursor_condition is not None:
            query = query.where(self.cursor_condition())
        query = query.order_by(self.cursor_order)
        return query.limit(self.first + 1)

    def compute_page_info(self, rows: list[Row], total_count: int) -> PageInfoResult[Row]:
        """Compute pagination info for cursor-based forward pagination."""

        # has_previous_page is True only if cursor was provided (meaning we're past the first page)
        has_previous_page = self.cursor_condition is not None
        has_next_page = len(rows) > self.first
        if has_next_page:
            rows = rows[: self.first]
        return PageInfoResult(
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
    - cursor_condition: Optional QueryCondition for WHERE clause (e.g., id < cursor_id).
      If None, starts from the end.
    - cursor_order: QueryOrder for cursor-based ordering (e.g., created_at DESC for reverse fetch)
    """

    last: int
    """Number of items to return (must be positive)."""

    cursor_order: QueryOrder
    """Ordering for cursor-based pagination (e.g., ORDER BY created_at DESC)."""

    cursor_condition: Optional[QueryCondition] = None
    """Optional QueryCondition for cursor position. If None, starts from the end."""

    @property
    def uses_window_function(self) -> bool:
        return False

    def apply(self, query: sa.sql.Select) -> sa.sql.Select:
        """
        Apply cursor-based backward pagination to query.

        Applies cursor condition (if present), cursor order, and LIMIT + 1 for has_previous_page detection.
        """
        if self.cursor_condition is not None:
            query = query.where(self.cursor_condition())
        query = query.order_by(self.cursor_order)
        return query.limit(self.last + 1)

    def compute_page_info(self, rows: list[Row], total_count: int) -> PageInfoResult[Row]:
        """Compute pagination info for cursor-based backward pagination."""

        # has_next_page is True only if cursor was provided (meaning there are items after this page)
        has_next_page = self.cursor_condition is not None
        has_previous_page = len(rows) > self.last
        if has_previous_page:
            rows = rows[: self.last]
        return PageInfoResult(
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

    Note:
        For cursor-based pagination, the pagination.apply() method applies
        cursor_order first. User-specified orders are applied after,
        serving as secondary sort criteria.
    """
    # Apply all conditions
    for condition in querier.conditions:
        query = query.where(condition())

    # Apply pagination (includes cursor condition and cursor_order for cursor pagination)
    query = querier.pagination.apply(query)

    # Apply user orders AFTER default order from pagination
    for order in querier.orders:
        query = query.order_by(order)

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

    For offset pagination, uses count().over() window function for efficient counting.
    For cursor pagination, executes a separate count query with filter conditions.

    Args:
        db_sess: Database session
        query: Base SELECT query (without count window function)
        querier: Querier for filtering, ordering, and pagination

    Returns:
        QuerierResult containing rows, total_count, and pagination info
    """
    initial_query = query

    # Add window function for offset pagination
    if querier.pagination.uses_window_function:
        query = query.add_columns(sa.func.count().over().label("total_count"))

    # Apply conditions and pagination to get data rows
    query = _apply_querier(query, querier)
    result = await db_sess.execute(query)
    rows = list(result.all())

    total_count: int
    if querier.pagination.uses_window_function and rows:
        # Offset pagination with results: use window function from rows
        total_count = rows[0].total_count
    else:
        # Cursor pagination or offset fallback (rows empty):
        # Execute pure count query with filter conditions only
        count_query = sa.select(sa.func.count()).select_from(initial_query.froms[0])
        for condition in querier.conditions:
            count_query = count_query.where(condition())

        count_result = await db_sess.execute(count_query)
        total_count = count_result.scalar() or 0

    # Calculate pagination info
    page_info = querier.pagination.compute_page_info(rows, total_count)

    return QuerierResult(
        rows=page_info.rows,
        total_count=total_count,
        has_next_page=page_info.has_next_page,
        has_previous_page=page_info.has_previous_page,
    )
