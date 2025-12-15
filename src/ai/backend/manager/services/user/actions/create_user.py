from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.user.types import UserCreateResultData
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.services.user.actions.base import UserAction


@dataclass
class CreateUserAction(UserAction):
    creator: Creator[UserRow]
    group_ids: Optional[list[str]] = None

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "create"


@dataclass
class CreateUserActionResult(BaseActionResult):
    data: UserCreateResultData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.user.id)
