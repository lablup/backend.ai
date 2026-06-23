from dataclasses import dataclass
from typing import override

from ai.backend.common.types import SessionId
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.session.base import SessionAction


@dataclass
class ResolveSessionNameAction(SessionAction):
    session_id: SessionId

    @override
    def entity_id(self) -> str | None:
        return str(self.session_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class ResolveSessionNameActionResult(BaseActionResult):
    session_name: str

    @override
    def entity_id(self) -> str | None:
        return None
