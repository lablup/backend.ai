from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.role_preset.types import RolePresetData
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.role_preset.actions.base import RolePresetAction


@dataclass
class UpdateRolePresetAction(RolePresetAction):
    updater: Updater[RolePresetRow]

    @override
    def entity_id(self) -> str | None:
        return str(self.updater.pk_value)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpdateRolePresetActionResult(BaseActionResult):
    preset: RolePresetData

    @override
    def entity_id(self) -> str | None:
        return str(self.preset.id)
