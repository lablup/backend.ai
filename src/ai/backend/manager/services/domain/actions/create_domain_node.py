from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.domain.types import (
    DomainData,
    UserInfo,
)
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.services.domain.actions.base import DomainAction


@dataclass
class CreateDomainNodeAction(DomainAction):
    user_info: UserInfo
    creator: Creator[DomainRow]
    scaling_groups: list[str] | None = None

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreateDomainNodeActionResult(BaseActionResult):
    domain_data: DomainData

    @override
    def entity_id(self) -> str | None:
        return self.domain_data.name
