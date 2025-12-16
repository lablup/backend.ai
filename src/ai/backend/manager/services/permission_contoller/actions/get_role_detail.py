from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.permission.role import RoleDetailData
from ai.backend.manager.services.permission_contoller.actions.base import RoleAction


@dataclass
class GetRoleDetailAction(RoleAction):
    role_id: UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.role_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_detail"


@dataclass
class GetRoleDetailActionResult(BaseActionResult):
    role: RoleDetailData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.role.id)
