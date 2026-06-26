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
from typing import TYPE_CHECKING, Any

import sqlalchemy as sa

from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.errors.repository import (
    ConditionalMutationForbidden,
    EmptySearchScopeError,
    UnsupportedCompositePrimaryKeyError,
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
    BulkConditionalCreator,
    BulkConditionalPurger,
    BulkConditionalUpdater,
    BulkCreator,
    BulkCreatorError,
    BulkCreatorResult,
    BulkCreatorResultWithFailures,
    BulkPurgerError,
    BulkPurgerResultWithFailures,
    BulkUpdaterError,
    BulkUpdaterResult,
    Creator,
    CreatorResult,
    DependentCreatorSpec,
    ExistsQuerier,
    NextValuePolicy,
    Purger,
    PurgerResult,
    Querier,
    QuerierResult,
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
    execute_querier,
    execute_upserter,
    match_integrity_error,
    parse_integrity_error,
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

    async def exists[TRow: Base](self, querier: ExistsQuerier[TRow]) -> bool:
        """Whether any row matches the querier's conditions.

        Runs ``SELECT EXISTS(SELECT 1 FROM table WHERE ...)``; does not count or fetch rows.
        """
        inner = (
            sa.select(sa.literal(True))
            .select_from(querier.row_class.__table__)
            .where(*[condition() for condition in querier.conditions])
        )
        result = await self._sess.execute(sa.select(inner.exists()))
        return bool(result.scalar_one())

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

    async def bulk_conditional_create_partial[TRow: Base, TGateRow: Base](
        self,
        bulk: BulkConditionalCreator[TRow, TGateRow],
    ) -> BulkCreatorResultWithFailures[TRow]:
        """Insert each gated item independently — partial success.

        Per item: the ``only_if`` gate is checked (``SELECT EXISTS``), then the row is inserted
        inside a savepoint. A rejected gate (``ConditionalMutationForbidden``) or a failed insert
        records a failure and rolls back only that item; the rest proceed. Must be used inside
        ``write_ops()``.
        """
        successes: list[TRow] = []
        errors: list[BulkCreatorError[TRow]] = []
        for index, conditional in enumerate(bulk.specs):
            if not await self.exists(conditional.only_if):
                errors.append(
                    BulkCreatorError(
                        spec=conditional.spec,
                        exception=ConditionalMutationForbidden(
                            f"Conditional create rejected: gate failed for item at index {index}."
                        ),
                        index=index,
                    )
                )
                continue
            async with self._sess.begin_nested():
                try:
                    row = conditional.spec.build_row()
                    self._sess.add(row)
                    await self._sess.flush()
                    successes.append(row)
                except sa.exc.IntegrityError as e:
                    parsed = parse_integrity_error(e)
                    checks = conditional.spec.integrity_error_checks
                    if checks:
                        try:
                            match_integrity_error(parsed, checks)
                        except Exception as domain_error:
                            errors.append(
                                BulkCreatorError(
                                    spec=conditional.spec, exception=domain_error, index=index
                                )
                            )
                    else:
                        errors.append(
                            BulkCreatorError(spec=conditional.spec, exception=parsed, index=index)
                        )
                except Exception as e:
                    errors.append(BulkCreatorError(spec=conditional.spec, exception=e, index=index))
        return BulkCreatorResultWithFailures(successes=successes, errors=errors)

    async def bulk_conditional_update_partial[TRow: Base, TGateRow: Base](
        self,
        bulk: BulkConditionalUpdater[TRow, TGateRow],
    ) -> BulkUpdaterResult[TRow]:
        """Update each gated item independently — partial success.

        Per item: the ``only_if`` gate is checked, then the row is updated by primary key inside
        a savepoint. A rejected gate, a missing target (recorded as ``ObjectNotFound``), or a
        failed update records a failure and rolls back only that item; the rest proceed. Must be
        used inside ``write_ops()``.
        """
        successes: list[TRow] = []
        errors: list[BulkUpdaterError[TRow]] = []
        for index, conditional in enumerate(bulk.updaters):
            if not await self.exists(conditional.only_if):
                errors.append(
                    BulkUpdaterError(
                        spec=conditional.updater.spec,
                        exception=ConditionalMutationForbidden(
                            f"Conditional update rejected: gate failed for item at index {index}."
                        ),
                        index=index,
                    )
                )
                continue
            try:
                async with self._sess.begin_nested():
                    result = await self._execute_updater(conditional.updater)
                    if result is None:
                        errors.append(
                            BulkUpdaterError(
                                spec=conditional.updater.spec,
                                exception=ObjectNotFound(
                                    f"Update target not found for item at index {index}."
                                ),
                                index=index,
                            )
                        )
                    else:
                        successes.append(result.row)
            except Exception as e:
                errors.append(
                    BulkUpdaterError(spec=conditional.updater.spec, exception=e, index=index)
                )
        return BulkUpdaterResult(successes=successes, errors=errors)

    async def bulk_conditional_purge_partial[TRow: Base, TGateRow: Base](
        self,
        bulk: BulkConditionalPurger[TRow, TGateRow],
    ) -> BulkPurgerResultWithFailures[TRow]:
        """Delete each gated item independently — partial success.

        Per item: the ``only_if`` gate is checked, then the row is deleted by primary key inside
        a savepoint. A rejected gate, a missing target (recorded as ``ObjectNotFound``), or a
        failed delete records a failure and rolls back only that item; the rest proceed. Must be
        used inside ``write_ops()``.
        """
        successes: list[TRow] = []
        errors: list[BulkPurgerError[TRow]] = []
        for index, conditional in enumerate(bulk.purgers):
            if not await self.exists(conditional.only_if):
                errors.append(
                    BulkPurgerError(
                        purger=conditional.purger,
                        exception=ConditionalMutationForbidden(
                            f"Conditional purge rejected: gate failed for item at index {index}."
                        ),
                        index=index,
                    )
                )
                continue
            try:
                async with self._sess.begin_nested():
                    result = await self._execute_purger(conditional.purger)
                    if result is None:
                        errors.append(
                            BulkPurgerError(
                                purger=conditional.purger,
                                exception=ObjectNotFound(
                                    f"Purge target not found for item at index {index}."
                                ),
                                index=index,
                            )
                        )
                    else:
                        successes.append(result.row)
            except Exception as e:
                errors.append(BulkPurgerError(purger=conditional.purger, exception=e, index=index))
        return BulkPurgerResultWithFailures(successes=successes, errors=errors)

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

    async def _execute_updater[TRow: Base](
        self, updater: Updater[TRow]
    ) -> UpdaterResult[TRow] | None:
        """Update a single row by primary key (shared by ``update`` and the bulk paths)."""
        row_class = updater.spec.row_class
        table = row_class.__table__
        pk_columns = list(table.primary_key.columns)
        if len(pk_columns) != 1:
            raise UnsupportedCompositePrimaryKeyError(
                "Updater only supports single-column primary keys",
            )
        values = updater.spec.build_values()
        if not values:
            # No columns to update: return the current row if it exists so callers can tell
            # "nothing to change" apart from "row not found". None means not found only.
            existing = await self._sess.execute(
                sa.select(row_class).where(pk_columns[0] == updater.pk_value)
            )
            current_row = existing.scalar_one_or_none()
            return UpdaterResult(row=current_row) if current_row is not None else None
        update_stmt = (
            sa.update(table)
            .values(values)
            .where(pk_columns[0] == updater.pk_value)
            .returning(*table.columns)
        )
        select_stmt = sa.select(row_class).from_statement(update_stmt)
        try:
            result = await self._sess.execute(select_stmt)
        except sa.exc.IntegrityError as e:
            parsed = parse_integrity_error(e)
            match_integrity_error(parsed, updater.spec.integrity_error_checks)
        updated_row = result.scalar_one_or_none()
        if updated_row is None:
            return None
        return UpdaterResult(row=updated_row)

    async def update[TRow: Base](self, updater: Updater[TRow]) -> UpdaterResult[TRow] | None:
        """Update a single row by primary key."""
        return await self._execute_updater(updater)

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

    async def _execute_purger[TRow: Base](self, purger: Purger[TRow]) -> PurgerResult[TRow] | None:
        """Delete a single row by primary key (shared by ``purge`` and the bulk paths)."""
        row_class = purger.row_class
        table = row_class.__table__
        pk_columns = list(table.primary_key.columns)
        if len(pk_columns) != 1:
            raise UnsupportedCompositePrimaryKeyError(
                f"Purger only supports single-column primary keys (table: {table.name})",
            )
        stmt = sa.delete(table).where(pk_columns[0] == purger.pk_value).returning(*table.columns)
        try:
            result = await self._sess.execute(stmt)
        except sa.exc.IntegrityError as e:
            raise parse_integrity_error(e) from e
        row_data = result.fetchone()
        if row_data is None:
            return None
        deleted_row: TRow = row_class(**dict(row_data._mapping))
        return PurgerResult(row=deleted_row)

    async def purge[TRow: Base](self, purger: Purger[TRow]) -> PurgerResult[TRow] | None:
        """Delete a single row by primary key."""
        return await self._execute_purger(purger)

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
