"""DB ops provider.

Wraps an :class:`ExtendedAsyncSAEngine` and exposes a spec-only read surface.
The engine is isolated inside :class:`DBOpsProvider`; callers obtain a session-bound
:class:`ReadOps` via the ``read_ops()`` context manager and never touch the engine,
raw sessions, or raw SQLAlchemy statements. Writes go through the v2 ops.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from datetime import datetime
from typing import TYPE_CHECKING, Any

import sqlalchemy as sa

from ai.backend.manager.errors.repository import (
    EmptyOperationScopeError,
)
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    BatchQuerierResult,
    Querier,
    QuerierResult,
    Searcher,
    SearcherResult,
    execute_batch_querier,
    execute_querier,
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
        scopes: Sequence[OperationScope],
    ) -> BatchQuerierResult[Row[Any]]:
        """Run a filtered/ordered/paginated query restricted to the given scopes.

        At least one scope is required: an empty scope list would degrade into an
        unscoped global scan. Use :meth:`batch_query_in_global` for that, explicitly.
        """
        if not scopes:
            raise EmptyOperationScopeError(
                "batch_query_with_scopes requires at least one scope; "
                "use batch_query_in_global for an explicit unscoped global query."
            )
        return await execute_batch_querier(self._sess, query, querier, scopes)

    async def search_with_scopes[TRow: Base, TData](
        self,
        scopes: Sequence[OperationScope],
        searcher: Searcher[TRow, TData],
    ) -> SearcherResult[TData]:
        """Run a searcher restricted to the given scopes and return converted data.

        Same scope rules as :meth:`batch_query_with_scopes`; the searcher carries its
        own SELECT and row conversion, so no ORM row is returned to the caller.
        """
        if not scopes:
            raise EmptyOperationScopeError(
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
        scopes: Sequence[OperationScope],
    ) -> SearcherResult[TData]:
        result = await execute_batch_querier(self._sess, searcher.build_select(), searcher, scopes)
        return SearcherResult(
            # build_select selects a single entity, so the row's first element is TRow.
            items=[searcher.to_data(row[0]) for row in result.rows],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )


class DBOpsProvider:
    """Entry point that isolates the engine and hands out session-bound ops.

    The engine is private; the only surface is ``read_ops()``, which uses the
    READ COMMITTED isolation level.
    """

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @asynccontextmanager
    async def read_ops(self) -> AsyncIterator[ReadOps]:
        """Open a read-only transaction and yield read-only ops."""
        async with self._db.begin_readonly_session_read_committed() as sess:
            yield ReadOps(sess)
