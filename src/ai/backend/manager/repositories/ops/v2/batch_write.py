"""Batch writes of the v2 ops: condition-selected updates and purges."""

from __future__ import annotations

from collections.abc import Sequence
from typing import cast

import sqlalchemy as sa

from ai.backend.manager.errors.repository import (
    EmptyOperationScopeError,
)
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.models.specs.purger import DataBatchPurger
from ai.backend.manager.models.specs.updater import DataBatchUpdater
from ai.backend.manager.repositories.ops.v2.write_base import V2WriteOpsBase


class V2BatchWriteOps(V2WriteOpsBase):
    """Batch writes over scope-restricted or global selections."""

    async def batch_update_in_scopes[TRow: Base, TData](
        self, scopes: Sequence[OperationScope], updater: DataBatchUpdater[TRow, TData]
    ) -> list[TData]:
        """Update every matching row within ``scopes``; at least one is required.

        The scope conditions are injected into the statement itself, so the spec's
        conditions cannot widen the write past the scopes the caller named. Same
        combination rule as the scoped search: scope conditions form one OR group,
        AND-merged with the spec's conditions.
        """
        if not scopes:
            raise EmptyOperationScopeError(
                "batch_update_in_scopes requires at least one scope; "
                "use batch_update_in_global for an explicit unscoped batch update."
            )
        await self._validate_scope_existence(scopes)
        return await self._batch_update_returning(self._scopes_condition(scopes), updater)

    async def batch_update_in_global[TRow: Base, TData](
        self, updater: DataBatchUpdater[TRow, TData]
    ) -> list[TData]:
        """Update every matching row across the table, with NO scope filter.

        Carries the same authority requirement as the global search: superadmin
        endpoints or internal system operations only.
        """
        return await self._batch_update_returning(None, updater)

    async def batch_purge_in_scopes[TRow: Base, TData](
        self, scopes: Sequence[OperationScope], purger: DataBatchPurger[TRow, TData]
    ) -> list[TData]:
        """Delete every row the spec selects within ``scopes``; at least one is
        required. Scope conditions are injected into the selecting subquery.

        Carries no membership work: reserve it for global- and field-family
        entities until a scoped-family batch purge that deregisters exists.
        """
        if not scopes:
            raise EmptyOperationScopeError(
                "batch_purge_in_scopes requires at least one scope; "
                "use batch_purge_in_global for an explicit unscoped batch purge."
            )
        await self._validate_scope_existence(scopes)
        return await self._batch_purge_returning(self._scopes_condition(scopes), purger)

    async def batch_purge_in_global[TRow: Base, TData](
        self, purger: DataBatchPurger[TRow, TData]
    ) -> list[TData]:
        """Delete every row the spec selects across the table, with NO scope filter.

        Same authority requirement as the global search; same membership caveat as
        :meth:`batch_purge_in_scopes`.
        """
        return await self._batch_purge_returning(None, purger)

    async def _batch_update_returning[TRow: Base, TData](
        self,
        scope_condition: sa.ColumnElement[bool] | None,
        updater: DataBatchUpdater[TRow, TData],
    ) -> list[TData]:
        row_class = updater.row_class
        table = row_class.__table__
        stmt = sa.update(table).values(updater.build_values())
        if scope_condition is not None:
            stmt = stmt.where(scope_condition)
        for condition in updater.conditions():
            stmt = stmt.where(condition())
        stmt = stmt.returning(*table.columns)
        try:
            result = await self._sess.execute(stmt)
        except sa.exc.IntegrityError as e:
            self._match_integrity_error(
                self._parse_integrity_error(e), updater.integrity_error_checks
            )
        return [updater.to_data(row_class(**dict(r._mapping))) for r in result.fetchall()]

    async def _batch_purge_returning[TRow: Base, TData](
        self,
        scope_condition: sa.ColumnElement[bool] | None,
        purger: DataBatchPurger[TRow, TData],
        batch_size: int = 1000,
    ) -> list[TData]:
        base_subquery = purger.build_subquery()
        entity = base_subquery.column_descriptions[0]["entity"]
        table = sa.inspect(entity).local_table
        pk_columns = list(table.primary_key.columns)
        row_class = cast("type[TRow]", entity)

        await self._validate_conflict_checks(purger.conflict_checks())

        removed: list[TData] = []
        while True:
            selecting = purger.build_subquery()
            if scope_condition is not None:
                selecting = selecting.where(scope_condition)
            sub = selecting.subquery()
            pk_subquery = sa.select(*[sub.c[pk.key] for pk in pk_columns]).limit(batch_size)
            stmt = (
                sa.delete(table)
                .where(sa.tuple_(*pk_columns).in_(pk_subquery))
                .returning(*table.columns)
            )
            try:
                result = await self._sess.execute(stmt)
            except sa.exc.IntegrityError as e:
                raise self._parse_integrity_error(e) from e
            rows = result.fetchall()
            removed.extend(purger.to_data(row_class(**dict(r._mapping))) for r in rows)
            if len(rows) < batch_size:
                break
        return removed
