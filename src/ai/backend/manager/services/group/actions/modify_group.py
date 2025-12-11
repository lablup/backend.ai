from dataclasses import dataclass, field
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.group.types import GroupData, GroupModifier
from ai.backend.manager.services.group.actions.base import GroupAction
from ai.backend.manager.types import OptionalState


@dataclass
class ModifyGroupAction(GroupAction):
    group_id: UUID
    modifier: GroupModifier = field(default_factory=GroupModifier)
    user_update_mode: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    user_uuids: OptionalState[list[str]] = field(default_factory=OptionalState[list[str]].nop)

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.group_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "modify"

    def update_mode(self) -> Optional[str]:
        if self.user_uuids.optional_value():
            return self.user_update_mode.optional_value()
        return None


@dataclass
class ModifyGroupActionResult(BaseActionResult):
    data: Optional[GroupData]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id) if self.data else None
