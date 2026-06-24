"""Querier for repository queries."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

import sqlalchemy as sa

from ai.backend.manager.errors.repository import UnsupportedCompositePrimaryKeyError
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.query_types import QueryCondition, QueryOrder

from .pagination import PageInfoResult, QueryPagination
from .types import ExistenceCheck, SearchScope

if TYPE_CHECKING:
    from sqlalchemy.engine import Row
    from sqlalchemy.ext.asyncio import AsyncSession as SASession

TRow = TypeVar("TRow", bound=Base)


# =============================================================================
# Single-row Querier (by PK)
# =============================================================================


@dataclass
class Querier[TRow: Base]:
    """Single-row query by primary key.

    Attributes:
        row_class: ORM class for table access and PK detection.
        pk_value: Primary key value to identify the target row.
    """

    row_class: type[TRow]
    pk_value: UUID | str | int


@dataclass
class QuerierResult[TRow: Base]:
    """Result of executing a single-row query operation."""

    row: TRow


async def execute_querier[TRow: Base](
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
    table = row_class.__table__
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
class BatchQuerierResult[TRow: Base]:
    """Result of executing a batch query with querier."""

    rows: list[TRow]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass
class _QueryPair:
    query: sa.sql.Select[Any]
    count_query: sa.sql.Select[Any]


async def _validate_scope(
    db_sess: SASession,
    checks: list[ExistenceCheck[Any]],
) -> None:
    """Validate scope existence checks in a single query.

    Args:
        db_sess: Database session
        checks: List of existence checks to validate

    Raises:
        The error specified in the first failing ExistenceCheck.
    """
    if not checks:
        return

    select_clauses = [
        sa.exists().where(check.column == check.value).label(f"check_{i}")
        for i, check in enumerate(checks)
    ]
    result = await db_sess.execute(sa.select(*select_clauses))
    row = result.mappings().one()

    for i, check in enumerate(checks):
        if not row[f"check_{i}"]:
            raise check.error


def _apply_batch_querier(
    query: sa.sql.Select[Any],
    querier: BatchQuerier,
    or_conditions: Sequence[QueryCondition],
) -> _QueryPair:
    """Apply query conditions, orders, and pagination to a SQLAlchemy select statement.

    Args:
        query: The base SELECT statement
        querier: BatchQuerier containing conditions, orders, and pagination to apply
        or_conditions: Conditions forming a single OR group, AND-merged with
            `querier.conditions`. Pass an empty sequence to skip the OR group.

    Returns:
        _QueryPair with the data query (filtered + paginated + ordered) and the
        count query (filtered only, no pagination/ordering).

    Note:
        Final WHERE applied to both data and count queries:
            (cond_1 AND ... AND cond_N) AND (or_1 OR ... OR or_M)
        For cursor-based pagination, the pagination.apply() method applies
        cursor_order first. User-specified orders are applied after,
        serving as secondary sort criteria.
    """
    count_query = sa.select(sa.func.count()).select_from(query.froms[0])

    for condition in querier.conditions:
        query = query.where(condition())
        count_query = count_query.where(condition())
    if or_conditions:
        query = query.where(sa.or_(*(c() for c in or_conditions)))
        count_query = count_query.where(sa.or_(*(c() for c in or_conditions)))

    # Apply pagination (includes cursor condition and cursor_order for cursor pagination)
    query = querier.pagination.apply(query)

    # Apply user orders AFTER default order from pagination
    for order in querier.orders:
        query = query.order_by(order)

    return _QueryPair(query=query, count_query=count_query)


async def execute_batch_querier(
    db_sess: SASession,
    query: sa.sql.Select[Any],
    querier: BatchQuerier,
    scopes: Sequence[SearchScope] = (),
) -> BatchQuerierResult[Row[Any]]:
    """Execute query with batch querier and return rows with total_count and pagination info.

    For offset pagination, uses count().over() window function for efficient counting.
    For cursor pagination, executes a separate count query with filter conditions.

    Args:
        db_sess: Database session
        query: Base SELECT query (without count window function)
        querier: BatchQuerier for filtering, ordering, and pagination
        scopes: Optional sequence of SearchScope. Each scope contributes its own
            existence checks (aggregated and validated in a single query) and its
            own to_condition() result. The to_condition() results form a single
            OR group that is AND-merged with querier.conditions.

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
    or_conditions: list[QueryCondition] = []
    if scopes:
        aggregated_checks: list[ExistenceCheck[Any]] = []
        for scope in scopes:
            aggregated_checks.extend(scope.existence_checks)
            or_conditions.append(scope.to_condition())
        await _validate_scope(db_sess, aggregated_checks)

    query_pair = _apply_batch_querier(query, querier, or_conditions)
    data_query = query_pair.query
    count_query = query_pair.count_query

    if querier.pagination.uses_window_function:
        data_query = data_query.add_columns(sa.func.count().over().label("total_count"))
    result = await db_sess.execute(data_query)
    rows = list(result.all())

    total_count: int
    if querier.pagination.uses_window_function and rows:
        # Offset pagination with results: use window function from rows
        total_count = rows[0].total_count
    else:
        # Cursor pagination or offset fallback (rows empty): separate count query
        count_result = await db_sess.execute(count_query)
        total_count = count_result.scalar() or 0

    # Calculate pagination info
    page_info: PageInfoResult[Row[Any]] = querier.pagination.compute_page_info(rows, total_count)

    return BatchQuerierResult(
        rows=page_info.rows,
        total_count=total_count,
        has_next_page=page_info.has_next_page,
        has_previous_page=page_info.has_previous_page,
    )
