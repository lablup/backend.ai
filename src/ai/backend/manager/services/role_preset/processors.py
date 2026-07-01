from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validators import ActionValidators
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
from ai.backend.manager.services.role_preset.actions.search_permission_presets import (
    SearchRolePermissionPresetsAction,
    SearchRolePermissionPresetsActionResult,
)
from ai.backend.manager.services.role_preset.actions.update import (
    UpdateRolePresetAction,
    UpdateRolePresetActionResult,
)
from ai.backend.manager.services.role_preset.service import RolePresetService


class RolePresetProcessors(AbstractProcessorPackage):
    create: ActionProcessor[CreateRolePresetAction, CreateRolePresetActionResult]
    get: ActionProcessor[GetRolePresetAction, GetRolePresetActionResult]
    search: ActionProcessor[SearchRolePresetsAction, SearchRolePresetsActionResult]
    search_permission_presets: ActionProcessor[
        SearchRolePermissionPresetsAction, SearchRolePermissionPresetsActionResult
    ]
    update: ActionProcessor[UpdateRolePresetAction, UpdateRolePresetActionResult]
    bulk_delete: ActionProcessor[BulkDeleteRolePresetsAction, BulkDeleteRolePresetsActionResult]
    bulk_restore: ActionProcessor[BulkRestoreRolePresetsAction, BulkRestoreRolePresetsActionResult]
    purge: ActionProcessor[PurgeRolePresetAction, PurgeRolePresetActionResult]
    bulk_purge: ActionProcessor[BulkPurgeRolePresetsAction, BulkPurgeRolePresetsActionResult]
    bulk_add_permissions: ActionProcessor[
        BulkAddRolePermissionPresetsAction, BulkAddRolePermissionPresetsActionResult
    ]
    bulk_remove_permissions: ActionProcessor[
        BulkRemoveRolePermissionPresetsAction, BulkRemoveRolePermissionPresetsActionResult
    ]

    def __init__(
        self,
        service: RolePresetService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
    ) -> None:
        self.create = ActionProcessor(service.create, action_monitors)
        self.get = ActionProcessor(service.get, action_monitors)
        self.search = ActionProcessor(service.search, action_monitors)
        self.search_permission_presets = ActionProcessor(
            service.search_permission_presets, action_monitors
        )
        self.update = ActionProcessor(service.update, action_monitors)
        self.bulk_delete = ActionProcessor(service.bulk_delete, action_monitors)
        self.bulk_restore = ActionProcessor(service.bulk_restore, action_monitors)
        self.purge = ActionProcessor(service.purge, action_monitors)
        self.bulk_purge = ActionProcessor(service.bulk_purge, action_monitors)
        self.bulk_add_permissions = ActionProcessor(service.bulk_add_permissions, action_monitors)
        self.bulk_remove_permissions = ActionProcessor(
            service.bulk_remove_permissions, action_monitors
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateRolePresetAction.spec(),
            GetRolePresetAction.spec(),
            SearchRolePresetsAction.spec(),
            SearchRolePermissionPresetsAction.spec(),
            UpdateRolePresetAction.spec(),
            BulkDeleteRolePresetsAction.spec(),
            BulkRestoreRolePresetsAction.spec(),
            PurgeRolePresetAction.spec(),
            BulkPurgeRolePresetsAction.spec(),
            BulkAddRolePermissionPresetsAction.spec(),
            BulkRemoveRolePermissionPresetsAction.spec(),
        ]
