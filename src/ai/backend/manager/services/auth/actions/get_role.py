import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.auth.actions.base import AuthGlobalAction


@dataclass(frozen=True)
class PublicGetRoleAction(AuthGlobalAction):
    user_id: uuid.UUID
    group_id: uuid.UUID | None
    is_superadmin: bool
    is_admin: bool

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "public_get_role"


@dataclass(frozen=True)
class PublicGetRoleActionResult:
    global_role: str
    domain_role: str
    group_role: str | None
