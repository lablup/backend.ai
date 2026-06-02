from dataclasses import dataclass
from typing import override

from ai.backend.common.identifier.user import UserID
from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.auth.actions.base import AuthAction


@dataclass
class ResolveUserIDByAccessKeyAction(AuthAction):
    access_key: AccessKey

    @override
    def entity_id(self) -> str | None:
        return str(self.access_key)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class ResolveUserIDByAccessKeyResult(BaseActionResult):
    user_id: UserID

    @override
    def entity_id(self) -> str | None:
        return str(self.user_id)
