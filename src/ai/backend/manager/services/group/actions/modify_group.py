from dataclasses import dataclass, field
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.group.types import GroupData
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.group.actions.base import GroupAction
from ai.backend.manager.types import OptionalState


@dataclass
class ModifyGroupAction(GroupAction):
    updater: Updater[GroupRow]
    user_update_mode: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    user_uuids: OptionalState[list[str]] = field(default_factory=OptionalState[list[str]].nop)

    @override
    def entity_id(self) -> str | None:
        return str(self.updater.pk_value)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    def update_mode(self) -> str | None:
        if self.user_uuids.optional_value():
            return self.user_update_mode.optional_value()
        return None


@dataclass
class ModifyGroupActionResult(BaseActionResult):
    data: GroupData | None

    @override
    def entity_id(self) -> str | None:
        return str(self.data.id) if self.data else None
