from dataclasses import dataclass
from typing import override

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.auth.actions.base import AuthAction


@dataclass
class ResolveAccessKeyScopeAction(AuthAction):
    requester_access_key: str
    requester_role: UserRole
    requester_domain: str
    owner_access_key: str | None  # None = self

    @override
    def entity_id(self) -> str | None:
        return self.requester_access_key

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class ResolveAccessKeyScopeResult(BaseActionResult):
    requester_access_key: AccessKey
    owner_access_key: AccessKey

    @override
    def entity_id(self) -> str | None:
        return None
