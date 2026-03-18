from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.auth.actions.base import AuthAction


@dataclass
class UpdateFullNameAction(AuthAction):
    user_id: str
    full_name: str
    domain_name: str
    email: str

    @override
    def entity_id(self) -> str | None:
        return str(self.user_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpdateFullNameActionResult(BaseActionResult):
    success: bool

    @override
    def entity_id(self) -> str | None:
        return None
