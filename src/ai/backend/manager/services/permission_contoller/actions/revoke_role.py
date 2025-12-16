from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.permission.role import (
    UserRoleRevocationData,
    UserRoleRevocationInput,
)
from ai.backend.manager.services.permission_contoller.actions.base import RoleAction


@dataclass
class RevokeRoleAction(RoleAction):
    input: UserRoleRevocationInput

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.input.user_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "revoke"


@dataclass
class RevokeRoleActionResult(BaseActionResult):
    data: UserRoleRevocationData

    @override
    def entity_id(self) -> Optional[str]:
        return None
