from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.auth.actions.base import AuthAction


@dataclass
class AdminUnblockUserAction(AuthAction):
    username: str

    @override
    def entity_id(self) -> str | None:
        return self.username

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class AdminUnblockUserActionResult(BaseActionResult):
    success: bool

    @override
    def entity_id(self) -> str | None:
        return None
