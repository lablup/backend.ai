from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.user.actions.base import UserAction


@dataclass
class DeleteUserAction(UserAction):
    email: str

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DeleteUserActionResult(BaseActionResult):
    @override
    def entity_id(self) -> str | None:
        return None
