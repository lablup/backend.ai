"""Database source for role preset repository operations.

Each public method only executes the spec/wrapper handed in by the caller —
no Creator/Updater/Purger objects are constructed here.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence

import sqlalchemy as sa

from ai.backend.common.identifier.role_permission_preset import RolePermissionPresetID
from ai.backend.common.identifier.role_preset import RolePresetID
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.common.bulk import (
    BulkCreateFailure,
    BulkPurgeFailure,
    BulkUpdateFailure,
)
from ai.backend.manager.data.role_preset.types import (
    RolePermissionPresetBulkAddResult,
    RolePermissionPresetBulkRemoveResult,
    RolePermissionPresetSearchResult,
    RolePresetBulkPurgeResult,
    RolePresetBulkUpdateResult,
    RolePresetData,
    RolePresetSearchResult,
)
from ai.backend.manager.errors.role_preset import RolePresetNotFound
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    BulkCreator,
    Creator,
    Purger,
    Querier,
)
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.ops import DBOpsProvider
from ai.backend.manager.repositories.role_preset.creators import (
    RolePermissionPresetDependentCreatorSpec,
    RolePresetCreatorSpec,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class RolePresetDBSource:
    _ops: DBOpsProvider

    def __init__(self, ops_provider: DBOpsProvider) -> None:
        self._ops = ops_provider

    async def create(
        self,
        creator_spec: RolePresetCreatorSpec,
        permission_creator_specs: Sequence[RolePermissionPresetDependentCreatorSpec],
    ) -> RolePresetData:
        async with self._ops.write_ops() as w:
            created = await w.create(Creator(spec=creator_spec))
            preset_row = created.row
            if permission_creator_specs:
                await w.bulk_create_dependent(permission_creator_specs, preset_row.id)
            return preset_row.to_data()

    async def get(self, preset_id: RolePresetID) -> RolePresetData:
        async with self._ops.read_ops() as r:
            result = await r.query(Querier(row_class=RolePresetRow, pk_value=preset_id))
            if result is None:
                raise RolePresetNotFound(f"Role preset with ID {preset_id} not found.")
            return result.row.to_data()

    async def search(
        self,
        querier: BatchQuerier,
    ) -> RolePresetSearchResult:
        async with self._ops.read_ops() as r:
            result = await r.batch_query_in_global(sa.select(RolePresetRow), querier)
            items = [row.RolePresetRow.to_data() for row in result.rows]
            return RolePresetSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def search_permission_presets(
        self,
        querier: BatchQuerier,
    ) -> RolePermissionPresetSearchResult:
        async with self._ops.read_ops() as r:
            result = await r.batch_query_in_global(sa.select(RolePermissionPresetRow), querier)
            items = [row.RolePermissionPresetRow.to_data() for row in result.rows]
            return RolePermissionPresetSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def update(
        self,
        updater: Updater[RolePresetRow],
    ) -> RolePresetData:
        async with self._ops.write_ops() as w:
            result = await w.update(updater)
            if result is None:
                raise RolePresetNotFound(f"Role preset with ID {updater.pk_value} not found.")
            return result.row.to_data()

    async def bulk_update(
        self,
        updaters: list[Updater[RolePresetRow]],
    ) -> RolePresetBulkUpdateResult:
        async with self._ops.write_ops() as w:
            result = await w.bulk_update_partial(updaters)
        successes = [row.to_data() for row in result.successes]
        failures = [BulkUpdateFailure(index=e.index, exception=e.exception) for e in result.errors]
        return RolePresetBulkUpdateResult(successes=successes, failures=failures)

    async def purge(self, preset_id: RolePresetID) -> bool:
        async with self._ops.write_ops() as w:
            result = await w.purge(Purger(row_class=RolePresetRow, pk_value=preset_id))
            return result is not None

    async def bulk_purge(
        self,
        ids: Sequence[RolePresetID],
    ) -> RolePresetBulkPurgeResult:
        purgers = [Purger(row_class=RolePresetRow, pk_value=preset_id) for preset_id in ids]
        async with self._ops.write_ops() as w:
            result = await w.bulk_purge_partial(purgers)
        successes = [row.to_data() for row in result.successes]
        failures = [BulkPurgeFailure(index=e.index, exception=e.exception) for e in result.errors]
        return RolePresetBulkPurgeResult(successes=successes, failures=failures)

    async def bulk_add_permissions(
        self,
        bulk_creator: BulkCreator[RolePermissionPresetRow],
    ) -> RolePermissionPresetBulkAddResult:
        if not bulk_creator.specs:
            return RolePermissionPresetBulkAddResult()
        async with self._ops.write_ops() as w:
            result = await w.bulk_create_partial(bulk_creator)
        successes = [row.to_data() for row in result.successes]
        failures = [BulkCreateFailure(index=e.index, exception=e.exception) for e in result.errors]
        return RolePermissionPresetBulkAddResult(successes=successes, failures=failures)

    async def bulk_remove_permissions(
        self,
        ids: Sequence[RolePermissionPresetID],
    ) -> RolePermissionPresetBulkRemoveResult:
        purgers = [Purger(row_class=RolePermissionPresetRow, pk_value=perm_id) for perm_id in ids]
        async with self._ops.write_ops() as w:
            result = await w.bulk_purge_partial(purgers)
        successes = [row.to_data() for row in result.successes]
        failures = [BulkPurgeFailure(index=e.index, exception=e.exception) for e in result.errors]
        return RolePermissionPresetBulkRemoveResult(successes=successes, failures=failures)
