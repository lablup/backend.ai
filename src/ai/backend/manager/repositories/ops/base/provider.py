"""DB ops provider.

Wraps an :class:`ExtendedAsyncSAEngine` and exposes a spec-only operations surface.
The engine is isolated inside :class:`DBOpsProvider`; callers obtain a session-bound
:class:`ReadOps` / :class:`WriteOps` via the ``read_ops()`` / ``write_ops()`` context
managers and never touch the engine, raw sessions, or raw SQLAlchemy statements.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from datetime import datetime
from typing import TYPE_CHECKING, Any, cast

import sqlalchemy as sa

from ai.backend.manager.errors.repository import (
    AmbiguousEntityKeyError,
    EmptySearchScopeError,
)
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.scopes import SearchScope
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import (
    BatchPurger,
    BatchPurgerResult,
    BatchQuerier,
    BatchQuerierResult,
    BatchUpdater,
    BatchUpdaterResult,
    BulkCreator,
    BulkCreatorResult,
    BulkCreatorResultWithFailures,
    BulkPurgerResultWithFailures,
    BulkUpdaterResult,
    Creator,
    CreatorResult,
    DataBatchPurger,
    DataBatchUpdater,
    DataCreator,
    DataFinder,
    DataPurger,
    DataQuerier,
    DataUpdater,
    DataUpserter,
    DependentCreatorSpec,
    NextValuePolicy,
    Purger,
    PurgerResult,
    Querier,
    QuerierResult,
    Searcher,
    SearcherResult,
    Updater,
    UpdaterResult,
    Upserter,
    UpserterResult,
    execute_batch_purger,
    execute_batch_querier,
    execute_batch_updater,
    execute_bulk_creator,
    execute_bulk_creator_partial,
    execute_bulk_dependent_creator,
    execute_bulk_purger_partial,
    execute_bulk_updater_partial,
    execute_creator,
    execute_dependent_creator,
    execute_next_value_creator,
    execute_purger,
    execute_querier,
    execute_updater,
    execute_upserter,
)
from ai.backend.manager.repositories.base.integrity import (
    match_integrity_error,
    parse_integrity_error,
)
from ai.backend.manager.repositories.base.purger import validate_conflict_checks
from ai.backend.manager.repositories.base.rbac.entity_creator import (
    RBACEntityCreator,
    RBACEntityCreatorResult,
    execute_rbac_entity_creator,
)
from ai.backend.manager.repositories.base.rbac.entity_purger import (
    RBACEntityPurger,
    RBACEntityPurgerResult,
    execute_rbac_entity_purger,
)

if TYPE_CHECKING:
    from sqlalchemy.engine import Row
    from sqlalchemy.ext.asyncio import AsyncSession as SASession


class ReadOps:
    """Read-only operations bound to a single session.

    Input is restricted to our spec types (Querier, BatchQuerier); raw SQLAlchemy
    statements are not accepted. The bound session is private and never exposed.
    """

    _sess: SASession

    def __init__(self, sess: SASession) -> None:
        self._sess = sess

    async def current_time(self) -> datetime:
        """DB-sourced current time, consistent across servers (not a per-server clock)."""
        result = await self._sess.execute(sa.select(sa.func.now()))
        return result.scalar_one()

    async def query[TRow: Base](self, querier: Querier[TRow]) -> QuerierResult[TRow] | None:
        """Fetch a single row by primary key."""
        return await execute_querier(self._sess, querier)

    async def query_data[TRow: Base, TData](
        self, querier: DataQuerier[TRow, TData]
    ) -> TData | None:
        """Fetch a single row by primary key and return it as its ``data/`` type.

        Converting counterpart of :meth:`query`, mirroring what :meth:`search_with_scopes`
        does for lists: the querier carries its own conversion, so the ORM row is
        consumed here and never reaches the caller.
        """
        result = await execute_querier(
            self._sess, Querier(row_class=querier.row_class(), pk_value=querier.pk_value())
        )
        if result is None:
            return None
        return querier.to_data(result.row)

    async def find_data[TRow: Base, TData](self, finder: DataFinder[TRow, TData]) -> TData | None:
        """Fetch one row by a key that is not its primary key, as its ``data/`` type.

        Reads at most two rows and rejects the second: a lookup key is expected to be
        unique, so more than one match means the conditions are wrong or the constraint
        that should enforce it is missing. Answering with an arbitrary one would hide
        both. No count is computed, unlike the search path.
        """
        row_class = finder.row_class()
        query = sa.select(row_class)
        for condition in finder.conditions():
            query = query.where(condition())
        result = await self._sess.execute(query.limit(2))
        rows = result.scalars().all()
        if not rows:
            return None
        if len(rows) > 1:
            raise AmbiguousEntityKeyError(
                f"The given key matches more than one {row_class.__name__}"
            )
        return finder.to_data(rows[0])

    async def batch_query_in_global(
        self,
        query: sa.sql.Select[Any],
        querier: BatchQuerier,
    ) -> BatchQuerierResult[Row[Any]]:
        """Run a filtered/ordered/paginated query across the entire table, with NO scope filter.

        WARNING: This bypasses RBAC scope restrictions and returns rows regardless of
        ownership. It is permitted ONLY for callers that already hold full authority —
        superadmin-only endpoints or internal system operations (e.g. schedulers,
        background reconciliation). For any request acting on behalf of a regular user,
        use :meth:`batch_query_with_scopes` instead. Choosing this method is an explicit,
        auditable decision to query globally; never use it as a convenience default.
        """
        return await execute_batch_querier(self._sess, query, querier)

    async def batch_query_with_scopes(
        self,
        query: sa.sql.Select[Any],
        querier: BatchQuerier,
        scopes: Sequence[SearchScope],
    ) -> BatchQuerierResult[Row[Any]]:
        """Run a filtered/ordered/paginated query restricted to the given scopes.

        At least one scope is required: an empty scope list would degrade into an
        unscoped global scan. Use :meth:`batch_query_in_global` for that, explicitly.
        """
        if not scopes:
            raise EmptySearchScopeError(
                "batch_query_with_scopes requires at least one scope; "
                "use batch_query_in_global for an explicit unscoped global query."
            )
        return await execute_batch_querier(self._sess, query, querier, scopes)

    async def search_with_scopes[TRow: Base, TData](
        self,
        scopes: Sequence[SearchScope],
        searcher: Searcher[TRow, TData],
    ) -> SearcherResult[TData]:
        """Run a searcher restricted to the given scopes and return converted data.

        Same scope rules as :meth:`batch_query_with_scopes`; the searcher carries its
        own SELECT and row conversion, so no ORM row is returned to the caller.
        """
        if not scopes:
            raise EmptySearchScopeError(
                "search_with_scopes requires at least one scope; "
                "use search_in_global for an explicit unscoped global search."
            )
        return await self._search(searcher, scopes)

    async def search_in_global[TRow: Base, TData](
        self,
        searcher: Searcher[TRow, TData],
    ) -> SearcherResult[TData]:
        """Run a searcher across the entire table, with NO scope filter.

        WARNING: carries the same authority requirement as
        :meth:`batch_query_in_global` — superadmin-only endpoints or internal system
        operations. For any request acting on behalf of a regular user, use
        :meth:`search_with_scopes` instead.
        """
        return await self._search(searcher, ())

    async def _search[TRow: Base, TData](
        self,
        searcher: Searcher[TRow, TData],
        scopes: Sequence[SearchScope],
    ) -> SearcherResult[TData]:
        result = await execute_batch_querier(self._sess, searcher.build_select(), searcher, scopes)
        return SearcherResult(
            items=[searcher.to_data(row) for row in result.rows],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )


class WriteOps(ReadOps):
    """Read-write operations bound to a single session."""

    async def create[TRow: Base](self, creator: Creator[TRow]) -> CreatorResult[TRow]:
        """Insert a single row."""
        return await execute_creator(self._sess, creator)

    async def create_data[TRow: Base, TData](self, creator: DataCreator[TRow, TData]) -> TData:
        """Insert a single row and return it as its ``data/`` type."""
        result = await execute_creator(self._sess, Creator(spec=creator))
        return creator.to_data(result.row)

    async def update_data[TRow: Base, TData](
        self, updater: DataUpdater[TRow, TData]
    ) -> TData | None:
        """Update a single row by primary key and return it as its ``data/`` type."""
        result = await execute_updater(
            self._sess, Updater(spec=updater, pk_value=updater.pk_value())
        )
        if result is None:
            return None
        return updater.to_data(result.row)

    async def purge_data[TRow: Base, TData](self, purger: DataPurger[TRow, TData]) -> TData | None:
        """Delete a single row by primary key and return it as its ``data/`` type."""
        result = await execute_purger(self._sess, Purger(spec=purger))
        if result is None:
            return None
        return purger.to_data(result.row)

    async def bulk_create_data[TRow: Base, TData](
        self, creators: Sequence[DataCreator[TRow, TData]]
    ) -> list[TData]:
        """Insert several rows atomically, returning them as their ``data/`` type.

        Takes a sequence of the same spec ``create_data`` takes rather than a spec of
        its own: a bulk create is N of them, and each already knows how its row converts.
        """
        if not creators:
            return []
        result = await execute_bulk_creator(self._sess, BulkCreator(specs=list(creators)))
        return [creator.to_data(row) for creator, row in zip(creators, result.rows, strict=True)]

    async def batch_update_data[TRow: Base, TData](
        self, updater: DataBatchUpdater[TRow, TData]
    ) -> list[TData]:
        """Update every row matching the spec's conditions, returning what was written.

        Converting counterpart of :meth:`batch_update`, which reports a row count. The
        rows come back through RETURNING because a scope-shaped run has to name the
        entities it touched, and a count cannot.
        """
        row_class = updater.row_class
        table = row_class.__table__
        stmt = sa.update(table).values(updater.build_values())
        for condition in updater.conditions():
            stmt = stmt.where(condition())
        stmt = stmt.returning(*table.columns)
        try:
            result = await self._sess.execute(stmt)
        except sa.exc.IntegrityError as e:
            parsed = parse_integrity_error(e)
            match_integrity_error(parsed, updater.integrity_error_checks)
        return [updater.to_data(row_class(**dict(r._mapping))) for r in result.fetchall()]

    async def batch_purge_data[TRow: Base, TData](
        self, purger: DataBatchPurger[TRow, TData], batch_size: int = 1000
    ) -> list[TData]:
        """Delete every row the spec's subquery selects, returning what was removed.

        Converting counterpart of :meth:`batch_purge`, deleting in chunks the same way
        so one call cannot hold a long transaction open. Every chunk's rows are
        accumulated, so the caller sees each entity the run removed rather than a count.
        """
        base_subquery = purger.build_subquery()
        entity = base_subquery.column_descriptions[0]["entity"]
        table = sa.inspect(entity).local_table
        pk_columns = list(table.primary_key.columns)
        row_class = cast(type[TRow], entity)

        await validate_conflict_checks(self._sess, purger.conflict_checks())

        removed: list[TData] = []
        while True:
            sub = purger.build_subquery().subquery()
            pk_subquery = sa.select(*[sub.c[pk.key] for pk in pk_columns]).limit(batch_size)
            stmt = (
                sa.delete(table)
                .where(sa.tuple_(*pk_columns).in_(pk_subquery))
                .returning(*table.columns)
            )
            try:
                result = await self._sess.execute(stmt)
            except sa.exc.IntegrityError as e:
                raise parse_integrity_error(e) from e
            rows = result.fetchall()
            removed.extend(purger.to_data(row_class(**dict(r._mapping))) for r in rows)
            if len(rows) < batch_size:
                break
        return removed

    async def bulk_create[TRow: Base](self, bulk: BulkCreator[TRow]) -> BulkCreatorResult[TRow]:
        """Insert multiple rows atomically (all-or-nothing)."""
        return await execute_bulk_creator(self._sess, bulk)

    async def bulk_create_partial[TRow: Base](
        self,
        bulk: BulkCreator[TRow],
    ) -> BulkCreatorResultWithFailures[TRow]:
        """Insert multiple rows, isolating each via a savepoint for partial success."""
        return await execute_bulk_creator_partial(self._sess, bulk)

    async def create_dependent[TDependency, TRow: Base](
        self,
        spec: DependentCreatorSpec[TDependency, TRow],
        dependency: TDependency,
    ) -> CreatorResult[TRow]:
        """Insert a single row that depends on a resolved value (e.g. a parent id).

        The caller builds ``dependency`` from a prior operation's result and passes it
        in; the spec's ``build_row`` receives it.
        """
        return await execute_dependent_creator(self._sess, spec, dependency)

    async def bulk_create_dependent[TDependency, TRow: Base](
        self,
        specs: Sequence[DependentCreatorSpec[TDependency, TRow]],
        dependency: TDependency,
    ) -> BulkCreatorResult[TRow]:
        """Insert rows that depend on a resolved value (e.g. a just-created parent id).

        The caller builds ``dependency`` from a prior operation's result and passes it
        in; every spec's ``build_row`` receives it. Keeps each spec single-table while
        the repository coordinates the multi-table sequence.
        """
        return await execute_bulk_dependent_creator(self._sess, specs, dependency)

    async def create_with_next_value[TRow: Base](
        self,
        policy: NextValuePolicy,
        spec: DependentCreatorSpec[int, TRow],
    ) -> CreatorResult[TRow]:
        """Insert a row assigning the next monotonic column value (e.g. rank), race-free.

        Locks the parent row (FOR UPDATE), computes ``MAX(column) + gap`` within the
        scope, and inserts via the spec — all within this write transaction so the lock
        and insert commit together. Must be used inside ``write_ops()``.
        """
        return await execute_next_value_creator(self._sess, policy, spec)

    async def update[TRow: Base](self, updater: Updater[TRow]) -> UpdaterResult[TRow] | None:
        """Update a single row by primary key."""
        return await execute_updater(self._sess, updater)

    async def batch_update[TRow: Base](self, updater: BatchUpdater[TRow]) -> BatchUpdaterResult:
        """Update all rows matching the updater conditions."""
        return await execute_batch_updater(self._sess, updater)

    async def bulk_update_partial[TRow: Base](
        self,
        updaters: Sequence[Updater[TRow]],
    ) -> BulkUpdaterResult[TRow]:
        """Update multiple rows by primary key, isolating each via a savepoint for partial success."""
        return await execute_bulk_updater_partial(self._sess, updaters)

    async def upsert[TRow: Base](
        self,
        upserter: Upserter[TRow],
        index_elements: list[str],
    ) -> UpserterResult[TRow]:
        """Insert or update a single row on conflict."""
        return await execute_upserter(self._sess, upserter, index_elements=index_elements)

    async def upsert_data[TRow: Base, TData](self, upserter: DataUpserter[TRow, TData]) -> TData:
        """Insert or update a single row on conflict, returning its ``data/`` type."""
        result = await execute_upserter(
            self._sess, Upserter(spec=upserter), index_elements=upserter.index_elements()
        )
        return upserter.to_data(result.row)

    async def create_rbac_entity[TRow: Base](
        self, creator: RBACEntityCreator[TRow]
    ) -> RBACEntityCreatorResult[TRow]:
        """Insert an entity row together with its RBAC scope association rows."""
        return await execute_rbac_entity_creator(self._sess, creator)

    async def purge_rbac_entity[TRow: Base](
        self, purger: RBACEntityPurger[TRow]
    ) -> RBACEntityPurgerResult[TRow] | None:
        """Delete an entity row along with its RBAC associations and permissions."""
        return await execute_rbac_entity_purger(self._sess, purger)

    async def purge[TRow: Base](self, purger: Purger[TRow]) -> PurgerResult[TRow] | None:
        """Delete a single row by primary key."""
        return await execute_purger(self._sess, purger)

    async def batch_purge[TRow: Base](self, purger: BatchPurger[TRow]) -> BatchPurgerResult:
        """Delete rows in batches matching the purger subquery."""
        return await execute_batch_purger(self._sess, purger)

    async def bulk_purge_partial[TRow: Base](
        self,
        purgers: list[Purger[TRow]],
    ) -> BulkPurgerResultWithFailures[TRow]:
        """Delete multiple rows individually, isolating each via a savepoint for partial success."""
        return await execute_bulk_purger_partial(self._sess, purgers)

    @asynccontextmanager
    async def savepoint(self) -> AsyncIterator[WriteOps]:
        """Open a nested transaction (savepoint) bound to the same session.

        A failure inside the block rolls back to the savepoint without aborting the
        enclosing transaction.
        """
        async with self._sess.begin_nested():
            yield WriteOps(self._sess)


class DBOpsProvider:
    """Entry point that isolates the engine and hands out session-bound ops.

    The engine is private; the only surface is ``read_ops()`` / ``write_ops()``.
    Both use the READ COMMITTED isolation level.
    """

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @asynccontextmanager
    async def read_ops(self) -> AsyncIterator[ReadOps]:
        """Open a read-only transaction and yield read-only ops."""
        async with self._db.begin_readonly_session_read_committed() as sess:
            yield ReadOps(sess)

    @asynccontextmanager
    async def write_ops(self) -> AsyncIterator[WriteOps]:
        """Open a read-write transaction and yield read-write ops."""
        async with self._db.begin_session_read_committed() as sess:
            yield WriteOps(sess)
