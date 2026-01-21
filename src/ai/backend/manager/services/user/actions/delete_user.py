from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.user.actions.base import UserAction


@dataclass
class DeleteUserAction(UserAction):
    email: str

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "delete"


@dataclass
class DeleteUserActionResult(BaseActionResult):
    @override
    def entity_id(self) -> Optional[str]:
        return None
