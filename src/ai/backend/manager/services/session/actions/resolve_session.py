import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.types import SessionId
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.session.base import SessionAction


@dataclass
class ResolveSessionAction(SessionAction):
    session_name: str
    user_id: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class ResolveSessionActionResult(BaseActionResult):
    session_id: SessionId

    @override
    def entity_id(self) -> str | None:
        return str(self.session_id)
