from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.login_session.types import LoginSessionData
from ai.backend.manager.services.login_session.actions.base import LoginSessionAction


@dataclass
class CreateLoginSessionAction(LoginSessionAction):
    user_uuid: UUID
    session_token: str
    client_ip: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreateLoginSessionActionResult(BaseActionResult):
    session: LoginSessionData

    @override
    def entity_id(self) -> str | None:
        return str(self.session.id)
