from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.domain.types import DomainData, UserInfo
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.domain.actions.base import DomainAction


@dataclass
class ModifyDomainNodeAction(DomainAction):
    user_info: UserInfo
    updater: Updater[DomainRow]
    sgroups_to_add: set[str] | None = None
    sgroups_to_remove: set[str] | None = None

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class ModifyDomainNodeActionResult(BaseActionResult):
    domain_data: DomainData

    @override
    def entity_id(self) -> str:
        return self.domain_data.name
