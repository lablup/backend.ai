from dataclasses import dataclass
from typing import override

from ai.backend.common.identifier.role_preset import RolePresetID
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.role_preset.actions.base import RolePresetAction


@dataclass
class PurgeRolePresetAction(RolePresetAction):
    preset_id: RolePresetID

    @override
    def entity_id(self) -> str | None:
        return str(self.preset_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE


@dataclass
class PurgeRolePresetActionResult(BaseActionResult):
    success: bool

    @override
    def entity_id(self) -> str | None:
        return None
