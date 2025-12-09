from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.permission.role import RoleCreateInput, RoleData
from ai.backend.manager.services.permission_contoller.actions.base import RoleAction


@dataclass
class CreateRoleAction(RoleAction):
    input: RoleCreateInput

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "create"


@dataclass
class CreateRoleActionResult(BaseActionResult):
    data: RoleData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id)
