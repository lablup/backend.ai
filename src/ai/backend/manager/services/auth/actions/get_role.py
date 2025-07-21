import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.auth.actions.base import AuthAction


@dataclass
class GetRoleAction(AuthAction):
    user_id: uuid.UUID
    group_id: Optional[uuid.UUID]
    is_superadmin: bool
    is_admin: bool

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.user_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_role"


@dataclass
class GetRoleActionResult(BaseActionResult):
    global_role: str
    domain_role: str
    group_role: Optional[str]

    @override
    def entity_id(self) -> Optional[str]:
        return None
