import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.auth.actions.base import AuthGlobalAction


@dataclass(frozen=True)
class PublicResolveUserScopeAction(AuthGlobalAction):
    requester_uuid: uuid.UUID
    requester_role: UserRole
    requester_domain: str
    is_superadmin: bool
    owner_user_email: str | None  # None = self

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "public_resolve_user_scope"


@dataclass(frozen=True)
class PublicResolveUserScopeResult:
    owner_uuid: uuid.UUID
    owner_role: UserRole
