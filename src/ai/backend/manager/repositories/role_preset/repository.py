from __future__ import annotations

import logging
from collections.abc import Sequence

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.role_preset.types import (
    RolePermissionPresetData,
    RolePresetData,
)
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
    Querier,
)
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.ops import DBOpsProvider
from ai.backend.manager.repositories.role_preset.creators import (
    RolePermissionPresetDependentCreatorSpec,
)
from ai.backend.manager.repositories.role_preset.db_source.db_source import (
    RolePresetDBSource,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class RolePresetRepository:
    _db_source: RolePresetDBSource

    def __init__(self, ops_provider: DBOpsProvider) -> None:
        self._db_source = RolePresetDBSource(ops_provider)

    async def create(
        self,
        creator: Creator[RolePresetRow],
        permission_creator_specs: Sequence[RolePermissionPresetDependentCreatorSpec],
    ) -> tuple[RolePresetData, list[RolePermissionPresetData]]:
        return await self._db_source.create(creator, permission_creator_specs)

    async def role_preset(self, querier: Querier[RolePresetRow]) -> RolePresetData:
        return await self._db_source.get(querier)

    async def search(
        self,
        querier: BatchQuerier,
    ) -> tuple[list[RolePresetData], int, bool, bool]:
        return await self._db_source.search(querier)

    async def update(self, updater: Updater[RolePresetRow]) -> RolePresetData:
        return await self._db_source.update(updater)

    async def bulk_delete(
        self,
        batch_updater: BatchUpdater[RolePresetRow],
    ) -> list[RolePresetData]:
        return await self._db_source.bulk_delete(batch_updater)

    async def bulk_restore(
        self,
        batch_updater: BatchUpdater[RolePresetRow],
    ) -> list[RolePresetData]:
        return await self._db_source.bulk_restore(batch_updater)

    async def bulk_purge(
        self,
        batch_purger: BatchPurger[RolePresetRow],
    ) -> list[RolePresetData]:
        return await self._db_source.bulk_purge(batch_purger)

    async def bulk_add_permissions(
        self,
        bulk_creator: BulkCreator[RolePermissionPresetRow],
    ) -> list[RolePermissionPresetData]:
        return await self._db_source.bulk_add_permissions(bulk_creator)

    async def bulk_remove_permissions(
        self,
        batch_purger: BatchPurger[RolePermissionPresetRow],
    ) -> list[RolePermissionPresetData]:
        return await self._db_source.bulk_remove_permissions(batch_purger)
