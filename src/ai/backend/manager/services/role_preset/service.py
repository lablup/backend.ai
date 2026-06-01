import logging

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.repositories.role_preset.repository import RolePresetRepository
from ai.backend.manager.services.role_preset.actions.bulk_add_permissions import (
    BulkAddRolePermissionPresetsAction,
    BulkAddRolePermissionPresetsActionResult,
)
from ai.backend.manager.services.role_preset.actions.bulk_purge import (
    BulkPurgeRolePresetsAction,
    BulkPurgeRolePresetsActionResult,
)
from ai.backend.manager.services.role_preset.actions.bulk_remove_permissions import (
    BulkRemoveRolePermissionPresetsAction,
    BulkRemoveRolePermissionPresetsActionResult,
)
from ai.backend.manager.services.role_preset.actions.create import (
    CreateRolePresetAction,
    CreateRolePresetActionResult,
)
from ai.backend.manager.services.role_preset.actions.delete import (
    BulkDeleteRolePresetsAction,
    BulkDeleteRolePresetsActionResult,
)
from ai.backend.manager.services.role_preset.actions.get import (
    GetRolePresetAction,
    GetRolePresetActionResult,
)
from ai.backend.manager.services.role_preset.actions.purge import (
    PurgeRolePresetAction,
    PurgeRolePresetActionResult,
)
from ai.backend.manager.services.role_preset.actions.restore import (
    BulkRestoreRolePresetsAction,
    BulkRestoreRolePresetsActionResult,
)
from ai.backend.manager.services.role_preset.actions.search import (
    SearchRolePresetsAction,
    SearchRolePresetsActionResult,
)
from ai.backend.manager.services.role_preset.actions.update import (
    UpdateRolePresetAction,
    UpdateRolePresetActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class RolePresetService:
    _repository: RolePresetRepository

    def __init__(self, repository: RolePresetRepository) -> None:
        self._repository = repository

    async def create(self, action: CreateRolePresetAction) -> CreateRolePresetActionResult:
        preset = await self._repository.create(action.creator_spec, action.permission_creator_specs)
        return CreateRolePresetActionResult(preset=preset)

    async def get(self, action: GetRolePresetAction) -> GetRolePresetActionResult:
        preset = await self._repository.role_preset(action.preset_id)
        return GetRolePresetActionResult(preset=preset)

    async def search(self, action: SearchRolePresetsAction) -> SearchRolePresetsActionResult:
        result = await self._repository.search(action.querier)
        return SearchRolePresetsActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def update(self, action: UpdateRolePresetAction) -> UpdateRolePresetActionResult:
        preset = await self._repository.update(action.updater)
        return UpdateRolePresetActionResult(preset=preset)

    async def bulk_delete(
        self, action: BulkDeleteRolePresetsAction
    ) -> BulkDeleteRolePresetsActionResult:
        result = await self._repository.bulk_update(action.updaters)
        return BulkDeleteRolePresetsActionResult(
            successes=result.successes,
            failures=result.failures,
        )

    async def bulk_restore(
        self, action: BulkRestoreRolePresetsAction
    ) -> BulkRestoreRolePresetsActionResult:
        result = await self._repository.bulk_update(action.updaters)
        return BulkRestoreRolePresetsActionResult(
            successes=result.successes,
            failures=result.failures,
        )

    async def purge(self, action: PurgeRolePresetAction) -> PurgeRolePresetActionResult:
        success = await self._repository.purge(action.preset_id)
        return PurgeRolePresetActionResult(success=success)

    async def bulk_purge(
        self, action: BulkPurgeRolePresetsAction
    ) -> BulkPurgeRolePresetsActionResult:
        result = await self._repository.bulk_purge(action.ids)
        return BulkPurgeRolePresetsActionResult(result=result)

    async def bulk_add_permissions(
        self, action: BulkAddRolePermissionPresetsAction
    ) -> BulkAddRolePermissionPresetsActionResult:
        result = await self._repository.bulk_add_permissions(action.bulk_creator)
        return BulkAddRolePermissionPresetsActionResult(
            successes=result.successes,
            failures=result.failures,
        )

    async def bulk_remove_permissions(
        self, action: BulkRemoveRolePermissionPresetsAction
    ) -> BulkRemoveRolePermissionPresetsActionResult:
        result = await self._repository.bulk_remove_permissions(action.ids)
        return BulkRemoveRolePermissionPresetsActionResult(
            successes=result.successes,
            failures=result.failures,
        )
