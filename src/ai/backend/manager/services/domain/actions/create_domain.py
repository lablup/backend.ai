from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.domain.types import DomainCreator, DomainData, UserInfo
from ai.backend.manager.services.domain.actions.base import DomainAction


@dataclass
class CreateDomainAction(DomainAction):
    creator: DomainCreator
    user_info: UserInfo

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "create"


@dataclass
class CreateDomainActionResult(BaseActionResult):
    domain_data: DomainData

    @override
    def entity_id(self) -> Optional[str]:
        return self.domain_data.name
