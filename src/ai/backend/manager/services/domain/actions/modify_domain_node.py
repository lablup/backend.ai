from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.domain.types import DomainData, UserInfo
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.domain.actions.base import DomainAction


@dataclass
class ModifyDomainNodeAction(DomainAction):
    user_info: UserInfo
    updater: Updater[DomainRow]
    sgroups_to_add: Optional[set[str]] = None
    sgroups_to_remove: Optional[set[str]] = None

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "modify"


@dataclass
class ModifyDomainNodeActionResult(BaseActionResult):
    domain_data: DomainData

    @override
    def entity_id(self):
        return self.domain_data.name
