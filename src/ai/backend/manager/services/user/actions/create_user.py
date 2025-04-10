from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.user.actions.base import UserAction
from ai.backend.manager.services.user.type import UserCreator, UserData


@dataclass
class CreateUserAction(UserAction):
    input: UserCreator

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "create"


@dataclass
class CreateUserActionResult(BaseActionResult):
    data: Optional[UserData]
    success: bool

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id) if self.data else None
