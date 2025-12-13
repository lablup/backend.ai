"""Querier for repository queries with pagination."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Generic

import sqlalchemy as sa

from .pagination import PageInfoResult, QueryPagination
from .types import QueryCondition, QueryOrder, TRow

if TYPE_CHECKING:
    from sqlalchemy.engine import Row
    from sqlalchemy.ext.asyncio import AsyncSession as SASession


@dataclass
class Querier:
    """Bundles query conditions, orders, and pagination for repository queries."""

    pagination: QueryPagination
    conditions: list[QueryCondition] = field(default_factory=list)
    orders: list[QueryOrder] = field(default_factory=list)


@dataclass
class QuerierResult(Generic[TRow]):
    """Result of executing a query with querier."""

    rows: list[TRow]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


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
    page_info: PageInfoResult[Row] = querier.pagination.compute_page_info(rows, total_count)

    return QuerierResult(
        rows=page_info.rows,
        total_count=total_count,
        has_next_page=page_info.has_next_page,
        has_previous_page=page_info.has_previous_page,
    )
