from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.domain.types import DomainData, UserInfo
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.domain.actions.base import DomainAction


@dataclass
class ModifyDomainAction(DomainAction):
    user_info: UserInfo
    updater: Updater[DomainRow]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "modify"


@dataclass
class ModifyDomainActionResult(BaseActionResult):
    domain_data: DomainData

    @override
    def entity_id(self) -> Optional[str]:
        return self.domain_data.name
