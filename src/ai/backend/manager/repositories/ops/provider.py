"""DB ops provider.

Wraps an :class:`ExtendedAsyncSAEngine` and exposes a spec-only operations surface.
The engine is isolated inside :class:`DBOpsProvider`; callers obtain a session-bound
:class:`ReadOps` / :class:`WriteOps` via the ``read_ops()`` / ``write_ops()`` context
managers and never touch the engine, raw sessions, or raw SQLAlchemy statements.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

import sqlalchemy as sa

from ai.backend.manager.errors.repository import EmptySearchScopeError
from ai.backend.manager.models.base import Base
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
    BulkUpdater,
    BulkUpdaterPartialResult,
    Creator,
    CreatorResult,
    DependentCreatorSpec,
    NextValuePolicy,
    Purger,
    PurgerResult,
    Querier,
    QuerierResult,
    SearchScope,
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
    execute_bulk_updater_partial,
    execute_creator,
    execute_dependent_creator,
    execute_next_value_creator,
    execute_purger,
    execute_querier,
    execute_updater,
    execute_upserter,
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

    async def query[TRow: Base](self, querier: Querier[TRow]) -> QuerierResult[TRow] | None:
        """Fetch a single row by primary key."""
        return await execute_querier(self._sess, querier)

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


class WriteOps(ReadOps):
    """Read-write operations bound to a single session."""

    async def create[TRow: Base](self, creator: Creator[TRow]) -> CreatorResult[TRow]:
        """Insert a single row."""
        return await execute_creator(self._sess, creator)

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

    async def upsert[TRow: Base](
        self,
        upserter: Upserter[TRow],
        index_elements: list[str],
    ) -> UpserterResult[TRow]:
        """Insert or update a single row on conflict."""
        return await execute_upserter(self._sess, upserter, index_elements=index_elements)

    async def purge[TRow: Base](self, purger: Purger[TRow]) -> PurgerResult[TRow] | None:
        """Delete a single row by primary key."""
        return await execute_purger(self._sess, purger)

    async def batch_purge[TRow: Base](self, purger: BatchPurger[TRow]) -> BatchPurgerResult:
        """Delete rows in batches matching the purger subquery."""
        return await execute_batch_purger(self._sess, purger)

    async def bulk_update_partial[TRow: Base](
        self,
        bulk: BulkUpdater[TRow],
    ) -> BulkUpdaterPartialResult[TRow]:
        """Update multiple rows, isolating each via a savepoint for partial success."""
        return await execute_bulk_updater_partial(self._sess, bulk)

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
