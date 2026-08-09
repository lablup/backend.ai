"""Update writes of the v2 ops: family-neutral single-row and bulk updates.

Updates never touch scope provisioning, so one update spec serves every family.
"""

from __future__ import annotations

from collections.abc import Mapping

from ai.backend.common.identifier.entity import EntityID
from ai.backend.manager.errors.repository import EntityNotFoundError
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.types import BulkResultWithFailures
from ai.backend.manager.models.specs.updater import DataUpdater
from ai.backend.manager.repositories.ops.v2.write_base import V2WriteOpsBase


class V2UpdateWriteOps(V2WriteOpsBase):
    """Family-neutral update writes, bound to a single session."""

    async def update_data[TRow: Base, TData](
        self, updater: DataUpdater[TRow, TData]
    ) -> TData | None:
        """Update a single row by primary key and return it as its ``data/`` type.

        Updates carry no scope work, so one update spec serves all families.
        """
        row = await self._update_row_returning(
            updater.row_class,
            updater.pk_value(),
            updater.build_values(),
            updater.integrity_error_checks,
        )
        if row is None:
            return None
        return updater.to_data(row)

    async def bulk_update_data[TRow: Base, TData](
        self, updaters: Mapping[EntityID, DataUpdater[TRow, TData]]
    ) -> BulkResultWithFailures[TData]:
        """Update each named entity independently in its own savepoint, reporting
        per entity — a missing row is an answer, not a gap."""
        successes: dict[EntityID, TData] = {}
        errors: dict[EntityID, Exception] = {}
        for entity_id, updater in updaters.items():
            try:
                async with self._sess.begin_nested():
                    row = await self._update_row_returning(
                        updater.row_class,
                        updater.pk_value(),
                        updater.build_values(),
                        updater.integrity_error_checks,
                    )
                    if row is None:
                        raise EntityNotFoundError(
                            f"{updater.row_class.__name__} {updater.pk_value()} not found"
                        )
                    successes[entity_id] = updater.to_data(row)
            except Exception as e:
                errors[entity_id] = e
        return BulkResultWithFailures(successes=successes, errors=errors)
