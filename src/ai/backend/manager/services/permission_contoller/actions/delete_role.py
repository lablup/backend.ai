from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.role import RoleData
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.permission_contoller.actions.base import RoleAction


@dataclass
class DeleteRoleAction(RoleAction):
    """Action for soft-deleting a role (status update)."""

    updater: Updater[RoleRow]

    @override
    def entity_id(self) -> str | None:
        return str(self.updater.pk_value)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DeleteRoleActionResult(BaseActionResult):
    data: RoleData

    @override
    def entity_id(self) -> str | None:
        return str(self.data.id)
