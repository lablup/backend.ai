from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.role_preset.types import RolePresetData
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.repositories.base import BatchUpdater
from ai.backend.manager.services.role_preset.actions.base import RolePresetAction


@dataclass
class BulkRestoreRolePresetsAction(RolePresetAction):
    batch_updater: BatchUpdater[RolePresetRow]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class BulkRestoreRolePresetsActionResult(BaseActionResult):
    presets: list[RolePresetData]

    @override
    def entity_id(self) -> str | None:
        return None
