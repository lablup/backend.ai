from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.group.types import GroupData
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.services.group.actions.base import GroupAction


@dataclass
class CreateGroupAction(GroupAction):
    creator: Creator[GroupRow]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "create"


@dataclass
class CreateGroupActionResult(BaseActionResult):
    data: Optional[GroupData]

    @override
    def entity_id(self) -> Optional[str]:
        return self.data.name if self.data is not None else None
