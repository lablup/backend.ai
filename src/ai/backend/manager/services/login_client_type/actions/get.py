from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.login_client_type.types import LoginClientTypeData
from ai.backend.manager.services.login_client_type.actions.base import LoginClientTypeAction


@dataclass
class GetLoginClientTypeAction(LoginClientTypeAction):
    id: UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetLoginClientTypeActionResult(BaseActionResult):
    login_client_type: LoginClientTypeData

    @override
    def entity_id(self) -> str | None:
        return str(self.login_client_type.id)
