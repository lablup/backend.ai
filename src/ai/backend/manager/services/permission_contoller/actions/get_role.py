from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.permission_contoller.actions.base import RoleAction


@dataclass
class GetRoleAction(RoleAction):
    user_id: UUID
    role_id: UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.role_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get"


@dataclass
class GetRoleActionResult(BaseActionResult):
    @override
    def entity_id(self) -> Optional[str]:
        return None
