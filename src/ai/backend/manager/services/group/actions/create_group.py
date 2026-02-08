from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.group.types import GroupData
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.services.group.actions.base import GroupAction


@dataclass
class CreateGroupAction(GroupAction):
    creator: Creator[GroupRow]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreateGroupActionResult(BaseActionResult):
    data: GroupData | None

    @override
    def entity_id(self) -> str | None:
        return self.data.name if self.data is not None else None
