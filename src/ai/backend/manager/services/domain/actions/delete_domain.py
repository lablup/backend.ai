from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.domain.types import UserInfo
from ai.backend.manager.services.domain.actions.base import DomainAction


@dataclass
class DeleteDomainAction(DomainAction):
    name: str
    user_info: UserInfo

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "delete"


@dataclass
class DeleteDomainActionResult(BaseActionResult):
    name: str

    @override
    def entity_id(self) -> Optional[str]:
        return None
