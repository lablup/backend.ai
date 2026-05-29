from __future__ import annotations

import logging
from collections.abc import Sequence

from ai.backend.common.identifier.role_preset import RolePresetID
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.role_preset.types import (
    RolePermissionPresetData,
    RolePresetBulkPurgeResult,
    RolePresetData,
    RolePresetSearchResult,
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
    ) -> RolePresetData:
        return await self._db_source.create(creator, permission_creator_specs)

    async def role_preset(self, preset_id: RolePresetID) -> RolePresetData:
        return await self._db_source.get(preset_id)

    async def search(
        self,
        querier: BatchQuerier,
    ) -> RolePresetSearchResult:
        return await self._db_source.search(querier)

    async def update(self, updater: Updater[RolePresetRow]) -> RolePresetData:
        return await self._db_source.update(updater)

    async def bulk_delete(
        self,
        batch_updater: BatchUpdater[RolePresetRow],
    ) -> int:
        return await self._db_source.bulk_delete(batch_updater)

    async def bulk_restore(
        self,
        batch_updater: BatchUpdater[RolePresetRow],
    ) -> int:
        return await self._db_source.bulk_restore(batch_updater)

    async def purge(self, preset_id: RolePresetID) -> bool:
        return await self._db_source.purge(preset_id)

    async def bulk_purge(
        self,
        ids: Sequence[RolePresetID],
    ) -> RolePresetBulkPurgeResult:
        return await self._db_source.bulk_purge(ids)

    async def bulk_add_permissions(
        self,
        bulk_creator: BulkCreator[RolePermissionPresetRow],
    ) -> list[RolePermissionPresetData]:
        return await self._db_source.bulk_add_permissions(bulk_creator)

    async def bulk_remove_permissions(
        self,
        batch_purger: BatchPurger[RolePermissionPresetRow],
    ) -> int:
        return await self._db_source.bulk_remove_permissions(batch_purger)
