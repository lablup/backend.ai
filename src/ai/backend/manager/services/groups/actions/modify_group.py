from dataclasses import dataclass, field
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.groups.actions.base import GroupAction
from ai.backend.manager.services.groups.types import GroupData, GroupModifier


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

    def get_modified_fields(self):
        return self.modifier.get_modified_fields()

    @property
    def user_update_mode(self):
        return self.modifier.user_update_mode

    @property
    def user_uuids(self):
        return self.modifier.user_uuids


@dataclass
class ModifyGroupActionResult(BaseActionResult):
    data: Optional[GroupData]
    success: bool

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id) if self.data else None
