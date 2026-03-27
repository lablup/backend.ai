from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.role import (
    UserRoleAssignmentData,
    UserRoleAssignmentInput,
)
from ai.backend.manager.services.permission_contoller.actions.base import RoleAction


@dataclass
class AssignRoleAction(RoleAction):
    input: UserRoleAssignmentInput

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.ROLE_ASSIGNMENT

    @override
    def entity_id(self) -> str | None:
        return str(self.input.user_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class AssignRoleActionResult(BaseActionResult):
    data: UserRoleAssignmentData

    @override
    def entity_id(self) -> str | None:
        return None
