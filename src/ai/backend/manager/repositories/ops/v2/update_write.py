"""Update writes of the v2 ops: single-row, guarded single-row, and bulk updates.

Updates never touch scope provisioning; the specs differ only in how the row to
write is picked.
"""

from __future__ import annotations

from collections.abc import Mapping

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.errors.repository import EntityNotFoundError
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.types import BulkResultWithFailures
from ai.backend.manager.models.specs.updater import DataUpdater, GuardedDataUpdater
from ai.backend.manager.repositories.ops.v2.write_base import V2WriteOpsBase


class V2UpdateWriteOps(V2WriteOpsBase):
    """Family-neutral update writes, bound to a single session."""

    async def update_data[TRow: Base, TData](
        self, updater: DataUpdater[TRow, TData]
    ) -> TData | None:
        """Update a single row by primary key and return it as its ``data/`` type.

        Updates carry no scope work, so one update spec serves every row.
        """
        row = await self._update_row_returning(
            updater.row_class,
            updater.target_id_column(),
            updater.target_id_value(),
            updater.build_values(),
            updater.integrity_error_checks,
        )
        if row is None:
            return None
        return updater.to_data(row)

    async def update_guarded_data[TRow: Base, TData](
        self, updater: GuardedDataUpdater[TRow, TData]
    ) -> TData | None:
        """Update the row the id names when its guard holds, returning what was
        written; ``None`` when nothing was — the row is gone or the guard refused.

        The guard rides on the statement, so no separate read and no row lock stand
        between the check and the write. Callers that must tell the two misses apart
        read the row themselves.
        """
        row_class = updater.row_class
        table = row_class.__table__
        values = updater.build_values()
        stmt = (
            sa.update(table)
            .values(values)
            .where(updater.target_id_column() == updater.target_id_value())
        )
        for condition in updater.guard_conditions():
            stmt = stmt.where(condition())
        stmt = stmt.returning(*table.columns)
        try:
            result = await self._sess.execute(sa.select(row_class).from_statement(stmt))
        except sa.exc.IntegrityError as e:
            self._match_integrity_error(
                self._parse_integrity_error(e), updater.integrity_error_checks
            )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return updater.to_data(row)

    async def partial_bulk_update_data[TRow: Base, TData](
        self, updaters: Mapping[EntityIdentifier, DataUpdater[TRow, TData]]
    ) -> BulkResultWithFailures[TData]:
        """Update each named entity independently in its own savepoint, reporting
        per entity — a missing row is an answer, not a gap."""
        successes: dict[EntityIdentifier, TData] = {}
        errors: dict[EntityIdentifier, Exception] = {}
        for entity_id, updater in updaters.items():
            try:
                async with self._sess.begin_nested():
                    row = await self._update_row_returning(
                        updater.row_class,
                        updater.target_id_column(),
                        updater.target_id_value(),
                        updater.build_values(),
                        updater.integrity_error_checks,
                    )
                    if row is None:
                        raise EntityNotFoundError(
                            f"{updater.row_class.__name__} {updater.target_id_value()} not found"
                        )
                    successes[entity_id] = updater.to_data(row)
            except Exception as e:
                errors[entity_id] = e
        return BulkResultWithFailures(successes=successes, errors=errors)
