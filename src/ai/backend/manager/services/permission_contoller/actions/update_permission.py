from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.models.rbac_models.permission.updaters import RolePermissionUpdater
from ai.backend.manager.services.permission_contoller.actions.permission import PermissionAction


@dataclass
class UpdatePermissionAction(PermissionAction):
    updater: RolePermissionUpdater

    @override
    def entity_id(self) -> str | None:
        return str(self.updater.target_id_value())

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpdatePermissionActionResult(BaseActionResult):
    data: PermissionData

    @override
    def entity_id(self) -> str | None:
        return str(self.data.id)
