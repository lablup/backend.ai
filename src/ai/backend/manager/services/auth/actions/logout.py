from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.auth.actions.base import AuthAction


@dataclass
class LogoutAction(AuthAction):
    session_token: str

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class LogoutActionResult(BaseActionResult):
    success: bool

    @override
    def entity_id(self) -> str | None:
        return None
