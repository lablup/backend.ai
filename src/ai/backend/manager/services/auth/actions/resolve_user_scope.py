import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.auth.actions.base import AuthAction


@dataclass
class ResolveUserScopeAction(AuthAction):
    requester_uuid: uuid.UUID
    requester_role: UserRole
    requester_domain: str
    is_superadmin: bool
    owner_user_email: str | None  # None = self

    @override
    def entity_id(self) -> str | None:
        return str(self.requester_uuid)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class ResolveUserScopeResult(BaseActionResult):
    owner_uuid: uuid.UUID
    owner_role: UserRole

    @override
    def entity_id(self) -> str | None:
        return None
