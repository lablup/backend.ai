from dataclasses import dataclass, field
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.group.actions.base import GroupAction
from ai.backend.manager.services.group.types import GroupData, GroupModifier


@dataclass
class ModifyGroupAction(GroupAction):
    group_id: UUID
    modifier: GroupModifier = field(default_factory=GroupModifier)

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.group_id)

    @override
    def operation_type(self) -> str:
        return "modify"


@dataclass
class ModifyGroupActionResult(BaseActionResult):
    data: Optional[GroupData]
    success: bool

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id) if self.data else None
