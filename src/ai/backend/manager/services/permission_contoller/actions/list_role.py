from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.permission.role import RoleData
from ai.backend.manager.services.permission_contoller.actions.base import RoleAction


@dataclass
class ListRoleAction(RoleAction):
    user_id: UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.user_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "list"


@dataclass
class GetRoleActionResult(BaseActionResult):
    roles: list[RoleData]

    @override
    def entity_id(self) -> Optional[str]:
        return None
