"""Batch writes of the v2 ops: condition-selected updates and purges."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.errors.repository import (
    EmptyOperationScopeError,
)
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.models.specs.purger import EntityBatchPurger
from ai.backend.manager.models.specs.updater import DataBatchUpdater
from ai.backend.manager.repositories.ops.v2.graph_write import V2GraphWriteOps


class V2BatchWriteOps(V2GraphWriteOps):
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

    async def batch_purge_entities_in_scopes[TRow: Base, TData](
        self, scopes: Sequence[OperationScope], purger: EntityBatchPurger[TRow, TData]
    ) -> list[TData]:
        """Delete every entity row the spec selects within ``scopes``, each with the
        RBAC graph it left; at least one scope is required."""
        if not scopes:
            raise EmptyOperationScopeError(
                "batch_purge_entities_in_scopes requires at least one scope; use "
                "batch_purge_entities_in_global for an explicit unscoped batch purge."
            )
        await self._validate_scope_existence(scopes)
        return await self._batch_purge_entities(self._scopes_condition(scopes), purger)

    async def batch_purge_entities_in_global[TRow: Base, TData](
        self, purger: EntityBatchPurger[TRow, TData]
    ) -> list[TData]:
        """Delete every entity row the spec selects across the table, each with the
        RBAC graph it left, with NO scope filter. Same authority requirement as the
        global search."""
        return await self._batch_purge_entities(None, purger)

    async def _batch_purge_entities[TRow: Base, TData](
        self,
        scope_condition: sa.ColumnElement[bool] | None,
        purger: EntityBatchPurger[TRow, TData],
    ) -> list[TData]:
        """The rows go first, then what each left in the graph, so a torn-down entity
        can never be one whose row survived."""
        entity_ids: list[EntityIdentifier] = []

        def collect(row: TRow) -> TData:
            entity_ids.append(purger.entity_id(row))
            return purger.to_data(row)

        removed = await self._batch_purge_returning(
            scope_condition, purger.build_subquery, purger.conflict_checks(), collect
        )
        for entity_id in entity_ids:
            await self._teardown(entity_id)
        return removed

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
