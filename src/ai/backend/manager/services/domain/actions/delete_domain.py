from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.domain.types import UserInfo
from ai.backend.manager.services.domain.actions.base import DomainAction


@dataclass
class DeleteDomainAction(DomainAction):
    name: str
    user_info: UserInfo

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DeleteDomainActionResult(BaseActionResult):
    name: str

    @override
    def entity_id(self) -> str | None:
        return None
