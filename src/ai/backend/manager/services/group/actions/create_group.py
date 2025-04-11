from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.group.actions.base import GroupAction
from ai.backend.manager.services.group.types import GroupCreator, GroupData


@dataclass
class CreateGroupAction(GroupAction):
    input: GroupCreator

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "create"


@dataclass
class CreateGroupActionResult(BaseActionResult):
    data: Optional[GroupData]
    success: bool

    @override
    def entity_id(self) -> Optional[str]:
        return self.data.name if self.data is not None else None
