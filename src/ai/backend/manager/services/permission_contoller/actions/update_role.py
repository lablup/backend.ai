from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.permission.role import RoleData, RoleUpdateInput
from ai.backend.manager.services.permission_contoller.actions.base import RoleAction


@dataclass
class UpdateRoleAction(RoleAction):
    input: RoleUpdateInput

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.input.id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "update"


@dataclass
class UpdateRoleActionResult(BaseActionResult):
    data: Optional[RoleData]
    success: bool

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id) if self.data else None
