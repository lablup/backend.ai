from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.services.session.base import SessionAction


@dataclass
class InterruptSessionAction(SessionAction):
    session_name: str
    owner_access_key: AccessKey

    @override
    @classmethod
    def action_name(cls) -> str:
        return "interrupt_session"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class InterruptSessionActionResult:
    # TODO: Add proper type
    result: Any
    session_data: SessionData
