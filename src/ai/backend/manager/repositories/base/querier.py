"""Querier for repository queries."""

from __future__ import annotations

import enum
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

import sqlalchemy as sa

from ai.backend.manager.errors.repository import UnsupportedCompositePrimaryKeyError
from ai.backend.manager.models.base import Base

from .pagination import PageInfoResult, QueryPagination
from .types import ExistenceCheck, QueryCondition, QueryOrder, SearchScope

if TYPE_CHECKING:
    from sqlalchemy.engine import Row
    from sqlalchemy.ext.asyncio import AsyncSession as SASession
    from sqlalchemy.orm import InstrumentedAttribute

TRow = TypeVar("TRow", bound=Base)


# =============================================================================
# Single-row Querier (by PK)
# =============================================================================


@dataclass
class Querier[TRow: Base]:
    """Single-row query by primary key (or an alternate unique column).

    Attributes:
        row_class: ORM class for table access and PK detection.
        pk_value: The value identifying the target row, matched against the
            primary key by default, or against ``lookup_column`` when set.
        lookup_column: Optional ORM attribute to match on instead of the
            primary key (e.g. ``RoutingRow.session`` for a 1:1 alternate key).
    """

    row_class: type[TRow]
    pk_value: UUID | str | int
    lookup_column: InstrumentedAttribute[Any] | None = None


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

    if querier.lookup_column is not None:
        match_column: Any = querier.lookup_column
    else:
        pk_columns = list(table.primary_key.columns)
        if len(pk_columns) != 1:
            raise UnsupportedCompositePrimaryKeyError(
                f"Querier only supports single-column primary keys (table: {table.name})",
            )
        match_column = pk_columns[0]

    stmt = sa.select(table).where(match_column == querier.pk_value)

    result = await db_sess.execute(stmt)
    row_data = result.fetchone()

    if row_data is None:
        return None

    fetched_row: TRow = row_class(**dict(row_data._mapping))
    return QuerierResult(row=fetched_row)


# =============================================================================
# Bulk single-row Querier (many independent by-key lookups)
# =============================================================================


class BulkQuerierFailureReason(enum.StrEnum):
    """Reason a single querier failed within a bulk execution."""

    NOT_FOUND = "not_found"


@dataclass
class QuerierFailureResult[TRow: Base]:
    """A single querier that could not be resolved, with the reason why."""

    querier: Querier[TRow]
    reason: BulkQuerierFailureReason


@dataclass
class BulkQuerierResult[TRow: Base]:
    """Partitioned outcome of a bulk querier execution.

    ``successes`` and ``failures`` together cover every input querier; both
    preserve the input order within their own list.
    """

    successes: list[QuerierResult[TRow]]
    failures: list[QuerierFailureResult[TRow]]


def _resolve_lookup_attr(querier: Querier[Any]) -> InstrumentedAttribute[Any]:
    """Resolve the ORM attribute a querier matches on (its lookup column, or PK)."""
    if querier.lookup_column is not None:
        return querier.lookup_column
    mapper = sa.inspect(querier.row_class)
    pk_columns = list(mapper.primary_key)
    if len(pk_columns) != 1:
        raise UnsupportedCompositePrimaryKeyError(
            f"Querier only supports single-column primary keys "
            f"(table: {querier.row_class.__tablename__})",
        )
    return getattr(querier.row_class, mapper.get_property_by_column(pk_columns[0]).key)


async def execute_bulk_querier[TRow: Base](
    db_sess: SASession,
    queriers: Sequence[Querier[TRow]],
    scopes: Sequence[SearchScope] = (),
) -> BulkQuerierResult[TRow]:
    """Execute many single-row queriers as a batch, partitioning the outcome.

    Queriers targeting the same ``row_class`` and lookup column are collapsed
    into one ``WHERE col IN (...)`` query, so the cost is one round-trip per
    distinct (row_class, column) group instead of one per querier — the bulk
    counterpart of :func:`execute_querier`. Each querier is then resolved
    independently: a matched row yields a ``QuerierResult`` (success), an
    unmatched one a ``QuerierFailureResult`` with ``NOT_FOUND`` (failure).

    ``scopes`` apply RBAC filtering exactly as in :func:`execute_batch_querier`:
    each scope contributes its existence checks (aggregated and validated once)
    and its ``to_condition()``; the conditions form a single OR group AND-merged
    with every group's ``IN`` predicate. A row filtered out by scope is treated
    as not found, so its querier lands in ``failures`` — no cross-scope leakage.

    Example:
        queriers = [
            Querier(row_class=RoutingRow, pk_value=sid, lookup_column=RoutingRow.session)
            for sid in session_ids
        ]
        result = await execute_bulk_querier(db_sess, queriers, scopes=[owned_scope])
        rows = [r.row for r in result.successes]  # found, in-scope routes
        missing = [f.querier.pk_value for f in result.failures]  # absent or out-of-scope
    """
    if not queriers:
        return BulkQuerierResult(successes=[], failures=[])

    or_conditions: list[QueryCondition] = []
    if scopes:
        aggregated_checks: list[ExistenceCheck[Any]] = []
        for scope in scopes:
            aggregated_checks.extend(scope.existence_checks)
            or_conditions.append(scope.to_condition())
        await _validate_scope(db_sess, aggregated_checks)

    # Group queriers by (row_class, lookup attribute) so each group is one IN-query.
    groups: dict[tuple[type[Base], str], list[Querier[TRow]]] = defaultdict(list)
    group_attr: dict[tuple[type[Base], str], InstrumentedAttribute[Any]] = {}
    for querier in queriers:
        attr = _resolve_lookup_attr(querier)
        key = (querier.row_class, attr.key)
        groups[key].append(querier)
        group_attr[key] = attr

    # One IN-query per group, AND-merged with the OR-combined scope predicate;
    # map lookup value -> fetched row.
    found: dict[tuple[type[Base], str], dict[Any, TRow]] = {}
    for key, group in groups.items():
        row_class, attr_key = key
        attr = group_attr[key]
        values = {querier.pk_value for querier in group}
        stmt = sa.select(row_class).where(attr.in_(values))
        if or_conditions:
            stmt = stmt.where(sa.or_(*(condition() for condition in or_conditions)))
        result = await db_sess.execute(stmt)
        found[key] = {getattr(row, attr_key): row for row in result.scalars().all()}

    # Resolve each querier in input order, keeping successes and failures apart.
    successes: list[QuerierResult[TRow]] = []
    failures: list[QuerierFailureResult[TRow]] = []
    for querier in queriers:
        key = (querier.row_class, _resolve_lookup_attr(querier).key)
        row = found[key].get(querier.pk_value)
        if row is None:
            failures.append(
                QuerierFailureResult(querier=querier, reason=BulkQuerierFailureReason.NOT_FOUND)
            )
        else:
            successes.append(QuerierResult(row=row))
    return BulkQuerierResult(successes=successes, failures=failures)


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
