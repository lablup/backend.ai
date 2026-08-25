from dataclasses import dataclass
from typing import override

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.auth.actions.base import AuthGlobalAction


@dataclass(frozen=True)
class PublicResolveAccessKeyScopeAction(AuthGlobalAction):
    requester_access_key: str
    requester_role: UserRole
    requester_domain: str
    owner_access_key: str | None  # None = self

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "public_resolve_access_key_scope"


@dataclass(frozen=True)
class PublicResolveAccessKeyScopeResult:
    requester_access_key: AccessKey
    owner_access_key: AccessKey
