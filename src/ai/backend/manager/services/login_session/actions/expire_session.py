from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.login_session.types import LoginSessionData, LoginSessionExpiryReason
from ai.backend.manager.services.login_session.actions.base import LoginSessionAction


@dataclass
class ExpireLoginSessionAction(LoginSessionAction):
    user_uuid: UUID
    session_token: str
    reason: LoginSessionExpiryReason

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class ExpireLoginSessionActionResult(BaseActionResult):
    session: LoginSessionData | None

    @override
    def entity_id(self) -> str | None:
        return str(self.session.id) if self.session else None
