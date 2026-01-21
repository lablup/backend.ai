"""Querier for repository queries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Generic, TypeVar
from uuid import UUID

import sqlalchemy as sa

from ai.backend.manager.errors.repository import UnsupportedCompositePrimaryKeyError
from ai.backend.manager.models.base import Base

from .pagination import PageInfoResult, QueryPagination
from .types import QueryCondition, QueryOrder

if TYPE_CHECKING:
    from sqlalchemy.engine import Row
    from sqlalchemy.ext.asyncio import AsyncSession as SASession

TRow = TypeVar("TRow", bound=Base)


# =============================================================================
# Single-row Querier (by PK)
# =============================================================================


@dataclass
class Querier(Generic[TRow]):
    """Single-row query by primary key.

    Attributes:
        row_class: ORM class for table access and PK detection.
        pk_value: Primary key value to identify the target row.
    """

    row_class: type[TRow]
    pk_value: UUID | str | int


@dataclass
class QuerierResult(Generic[TRow]):
    """Result of executing a single-row query operation."""

    row: TRow


async def execute_querier(
    db_sess: SASession,
    querier: Querier[TRow],
) -> QuerierResult[TRow] | None:
    """Execute SELECT for a single row by primary key.

    Args:
        db_sess: Database session
        querier: Querier containing row_class and pk_value

    Returns:
        QuerierResult containing the fetched row, or None if no row matched

    Example:
        querier = Querier(
            row_class=SessionRow,
            pk_value=session_id,
        )
        result = await execute_querier(db_sess, querier)
        if result:
            print(result.row.id)  # Fetched row
    """
    row_class = querier.row_class
    table = row_class.__table__  # type: ignore[attr-defined]
    pk_columns = list(table.primary_key.columns)

    if len(pk_columns) != 1:
        raise UnsupportedCompositePrimaryKeyError(
            f"Querier only supports single-column primary keys (table: {table.name})",
        )

    stmt = sa.select(table).where(pk_columns[0] == querier.pk_value)

    result = await db_sess.execute(stmt)
    row_data = result.fetchone()

    if row_data is None:
        return None

    fetched_row: TRow = row_class(**dict(row_data._mapping))
    return QuerierResult(row=fetched_row)


# =============================================================================
# Batch Querier (with pagination)
# =============================================================================


@dataclass
class BatchQuerier:
    """Bundles query conditions, orders, and pagination for batch repository queries."""

    pagination: QueryPagination
    conditions: list[QueryCondition] = field(default_factory=list)
    orders: list[QueryOrder] = field(default_factory=list)


@dataclass
class BatchQuerierResult(Generic[TRow]):
    """Result of executing a batch query with querier."""

    rows: list[TRow]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


def _apply_batch_querier(
    query: sa.sql.Select[Any],
    querier: BatchQuerier,
) -> sa.sql.Select[Any]:
    """Apply query conditions, orders, and pagination to a SQLAlchemy select statement.

    Args:
        query: The base SELECT statement
        querier: BatchQuerier containing conditions, orders, and pagination to apply

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


async def execute_batch_querier(
    db_sess: SASession,
    query: sa.sql.Select[Any],
    querier: BatchQuerier,
) -> BatchQuerierResult[Row]:
    """Execute query with batch querier and return rows with total_count and pagination info.

    For offset pagination, uses count().over() window function for efficient counting.
    For cursor pagination, executes a separate count query with filter conditions.

    Args:
        db_sess: Database session
        query: Base SELECT query (without count window function)
        querier: BatchQuerier for filtering, ordering, and pagination

    Returns:
        BatchQuerierResult containing rows, total_count, and pagination info

    Example:
        querier = BatchQuerier(
            pagination=OffsetPagination(offset=0, limit=10),
            conditions=[lambda: SessionRow.status == SessionStatus.RUNNING],
            orders=[SessionRow.created_at.desc()],
        )
        result = await execute_batch_querier(db_sess, sa.select(SessionRow), querier)
        print(result.rows)  # List of matching rows
        print(result.total_count)  # Total count
    """
    initial_query = query

    # Add window function for offset pagination
    if querier.pagination.uses_window_function:
        query = query.add_columns(sa.func.count().over().label("total_count"))

    # Apply conditions and pagination to get data rows
    query = _apply_batch_querier(query, querier)
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

    return BatchQuerierResult(
        rows=page_info.rows,
        total_count=total_count,
        has_next_page=page_info.has_next_page,
        has_previous_page=page_info.has_previous_page,
    )
