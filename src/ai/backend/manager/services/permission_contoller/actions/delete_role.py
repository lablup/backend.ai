from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.permission.role import (
    RoleDeleteInput,
)
from ai.backend.manager.services.permission_contoller.actions.base import RoleAction


@dataclass
class DeleteRoleAction(RoleAction):
    input: RoleDeleteInput

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.input.id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "delete"


@dataclass
class DeleteRoleActionResult(BaseActionResult):
    success: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None
