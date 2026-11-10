from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.session.base import SessionAction


@dataclass
class ResolveSessionNameAction(SessionAction):
    @override
    @classmethod
    def action_name(cls) -> str:
        return "resolve_session_name"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class ResolveSessionNameActionResult:
    session_name: str
