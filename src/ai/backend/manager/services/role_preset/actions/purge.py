from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.role_preset.types import RolePresetData
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.repositories.base import BatchPurger
from ai.backend.manager.services.role_preset.actions.base import RolePresetAction


@dataclass
class BulkPurgeRolePresetsAction(RolePresetAction):
    batch_purger: BatchPurger[RolePresetRow]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE


@dataclass
class BulkPurgeRolePresetsActionResult(BaseActionResult):
    presets: list[RolePresetData]

    @override
    def entity_id(self) -> str | None:
        return None
