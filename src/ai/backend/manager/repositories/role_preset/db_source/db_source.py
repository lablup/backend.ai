"""Database source for role preset repository operations.

Each public method only executes the spec/wrapper handed in by the caller —
no Creator/Updater/Purger objects are constructed here.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence

import sqlalchemy as sa

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.role_preset.types import (
    RolePermissionPresetData,
    RolePresetData,
)
from ai.backend.manager.errors.role_preset import RolePresetNotFound
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.repositories.base import (
    BatchPurger,
    BatchQuerier,
    BatchUpdater,
    BulkCreator,
    Creator,
    NoPagination,
    Querier,
)
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.ops import DBOpsProvider
from ai.backend.manager.repositories.role_preset.creators import (
    RolePermissionPresetDependentCreatorSpec,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class RolePresetDBSource:
    _ops: DBOpsProvider

    def __init__(self, ops_provider: DBOpsProvider) -> None:
        self._ops = ops_provider

    async def create(
        self,
        creator: Creator[RolePresetRow],
        permission_creator_specs: Sequence[RolePermissionPresetDependentCreatorSpec],
    ) -> tuple[RolePresetData, list[RolePermissionPresetData]]:
        async with self._ops.write_ops() as w:
            created = await w.create(creator)
            preset_row = created.row
            permission_rows: list[RolePermissionPresetRow] = []
            if permission_creator_specs:
                bulk_result = await w.bulk_create_dependent(permission_creator_specs, preset_row.id)
                permission_rows = list(bulk_result.rows)
            return (
                preset_row.to_data(),
                [row.to_data() for row in permission_rows],
            )

    async def get(self, querier: Querier[RolePresetRow]) -> RolePresetData:
        async with self._ops.read_ops() as r:
            result = await r.query(querier)
            if result is None:
                raise RolePresetNotFound()
            return result.row.to_data()

    async def search(
        self,
        querier: BatchQuerier,
    ) -> tuple[list[RolePresetData], int, bool, bool]:
        async with self._ops.read_ops() as r:
            result = await r.batch_query_in_global(sa.select(RolePresetRow), querier)
            items = [row.RolePresetRow.to_data() for row in result.rows]
            return (
                items,
                result.total_count,
                result.has_next_page,
                result.has_previous_page,
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

    async def bulk_delete(
        self,
        batch_updater: BatchUpdater[RolePresetRow],
    ) -> list[RolePresetData]:
        return await self._batch_update_and_refetch(batch_updater)

    async def bulk_restore(
        self,
        batch_updater: BatchUpdater[RolePresetRow],
    ) -> list[RolePresetData]:
        return await self._batch_update_and_refetch(batch_updater)

    async def _batch_update_and_refetch(
        self,
        batch_updater: BatchUpdater[RolePresetRow],
    ) -> list[RolePresetData]:
        async with self._ops.write_ops() as w:
            await w.batch_update(batch_updater)
            refetch_query = sa.select(RolePresetRow)
            for condition in batch_updater.conditions:
                refetch_query = refetch_query.where(condition())
            result = await w.batch_query_in_global(
                refetch_query, BatchQuerier(pagination=NoPagination())
            )
            return [row.RolePresetRow.to_data() for row in result.rows]

    async def bulk_purge(
        self,
        batch_purger: BatchPurger[RolePresetRow],
    ) -> list[RolePresetData]:
        async with self._ops.write_ops() as w:
            snapshot_query = batch_purger.spec.build_subquery()
            snapshot_result = await w.batch_query_in_global(
                snapshot_query, BatchQuerier(pagination=NoPagination())
            )
            snapshots = [row.RolePresetRow.to_data() for row in snapshot_result.rows]
            await w.batch_purge(batch_purger)
            return snapshots

    async def bulk_add_permissions(
        self,
        bulk_creator: BulkCreator[RolePermissionPresetRow],
    ) -> list[RolePermissionPresetData]:
        if not bulk_creator.specs:
            return []
        async with self._ops.write_ops() as w:
            result = await w.bulk_create(bulk_creator)
            return [row.to_data() for row in result.rows]

    async def bulk_remove_permissions(
        self,
        batch_purger: BatchPurger[RolePermissionPresetRow],
    ) -> list[RolePermissionPresetData]:
        async with self._ops.write_ops() as w:
            snapshot_query = batch_purger.spec.build_subquery()
            snapshot_result = await w.batch_query_in_global(
                snapshot_query, BatchQuerier(pagination=NoPagination())
            )
            snapshots = [row.RolePermissionPresetRow.to_data() for row in snapshot_result.rows]
            await w.batch_purge(batch_purger)
            return snapshots
