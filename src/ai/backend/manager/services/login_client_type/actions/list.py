from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.login_client_type.types import LoginClientTypeData
from ai.backend.manager.services.login_client_type.actions.base import LoginClientTypeAction


@dataclass
class ListLoginClientTypesAction(LoginClientTypeAction):
    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class ListLoginClientTypesActionResult(BaseActionResult):
    login_client_types: list[LoginClientTypeData]

    @override
    def entity_id(self) -> str | None:
        return None
