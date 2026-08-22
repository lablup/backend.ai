from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.services.session.base import (
    SessionAction,
)


@dataclass
class GetSessionAction(SessionAction):
    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_session"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetSessionActionResult:
    session_data: SessionData
