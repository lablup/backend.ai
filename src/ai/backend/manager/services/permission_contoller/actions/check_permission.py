from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.permission_contoller.actions.base import RoleAction


@dataclass
class CheckPermissionAction(RoleAction):
    user_id: UUID
    operation: str
    target_entity_type: str
    target_entity_id: str

    @override
    def entity_id(self) -> str | None:
        return str(self.user_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class CheckPermissionActionResult(BaseActionResult):
    has_permission: bool

    @override
    def entity_id(self) -> str | None:
        return None
