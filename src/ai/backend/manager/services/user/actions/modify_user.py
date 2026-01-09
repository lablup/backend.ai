from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.user.actions.base import UserAction


@dataclass
class ModifyUserAction(UserAction):
    email: str
    updater: Updater[UserRow]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "modify"


@dataclass
class ModifyUserActionResult(BaseActionResult):
    data: UserData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id)
