"""Update writes of the v2 ops: single-row and bulk updates.

Updates never touch scope provisioning; the specs differ only in how the row to
write is picked.
"""

from __future__ import annotations

from collections.abc import Mapping

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.types import BulkResultWithFailures
from ai.backend.manager.models.specs.updater import GuardedDataUpdater
from ai.backend.manager.repositories.ops.v2.write_base import V2WriteOpsBase


class V2UpdateWriteOps(V2WriteOpsBase):
    """Family-neutral update writes, bound to a single session."""

    async def update_data[TRow: Base, TData](
        self, updater: GuardedDataUpdater[TRow, TData]
    ) -> TData | None:
        """Update the row the id names while its guards hold, returning what was
        written; ``None`` when the row is gone, the failing guard's error when it
        refused.

        The guards ride on the statement, so no separate read and no row lock stand
        between the check and the write. Updates carry no scope work, so one update
        spec serves every row.
        """
        row = await self._update_row_returning(
            updater.row_class,
            updater.target_id_column(),
            updater.target_id_value(),
            updater.guard_checks(),
            updater.build_values(),
            updater.integrity_error_checks,
        )
        if row is None:
            return None
        return updater.to_data(row)

    async def partial_bulk_update_data[TRow: Base, TData](
        self, updaters: Mapping[EntityIdentifier, GuardedDataUpdater[TRow, TData]]
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
                        updater.guard_checks(),
                        updater.build_values(),
                        updater.integrity_error_checks,
                    )
                    if row is None:
                        raise EntityNotFoundError(
                            entity_type=entity_id.entity_type(),
                            operation=ActionOperationType.UPDATE,
                            extra_msg=f"{updater.row_class.__name__} {entity_id} not found",
                        )
                    successes[entity_id] = updater.to_data(row)
            except Exception as e:
                errors[entity_id] = e
        return BulkResultWithFailures(successes=successes, errors=errors)
