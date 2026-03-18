import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.auth.actions.base import AuthAction


@dataclass
class GetRoleAction(AuthAction):
    user_id: uuid.UUID
    group_id: uuid.UUID | None
    is_superadmin: bool
    is_admin: bool

    @override
    def entity_id(self) -> str | None:
        return str(self.user_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetRoleActionResult(BaseActionResult):
    global_role: str
    domain_role: str
    group_role: str | None

    @override
    def entity_id(self) -> str | None:
        return None
