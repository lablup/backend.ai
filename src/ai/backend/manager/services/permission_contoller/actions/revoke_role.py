from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.role import (
    UserRoleRevocationData,
    UserRoleRevocationInput,
)
from ai.backend.manager.services.permission_contoller.actions.base import RoleAction


@dataclass
class RevokeRoleAction(RoleAction):
    input: UserRoleRevocationInput

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
        return ActionOperationType.DELETE


@dataclass
class RevokeRoleActionResult(BaseActionResult):
    data: UserRoleRevocationData

    @override
    def entity_id(self) -> str | None:
        return None
