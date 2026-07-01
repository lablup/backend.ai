from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.login_client_type.types import LoginClientTypeData
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.services.login_client_type.actions.base import LoginClientTypeAction


@dataclass
class CreateLoginClientTypeAction(LoginClientTypeAction):
    creator: Creator[LoginClientTypeRow]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreateLoginClientTypeActionResult(BaseActionResult):
    login_client_type: LoginClientTypeData

    @override
    def entity_id(self) -> str | None:
        return str(self.login_client_type.id)
