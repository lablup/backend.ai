from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.group.types import GroupData
from ai.backend.manager.models.group.updaters import GroupUpdater
from ai.backend.manager.types import OptionalState


@dataclass(frozen=True)
class UpdateGroupAction(BaseSingleEntityAction):
    """Edit one project, optionally rewriting who belongs to it."""

    project_id: ProjectID
    updater: GroupUpdater
    user_update_mode: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    user_uuids: OptionalState[list[str]] = field(default_factory=OptionalState[list[str]].nop)

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.project_id

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_project"

    def update_mode(self) -> str | None:
        if self.user_uuids.optional_value():
            return self.user_update_mode.optional_value()
        return None


@dataclass(frozen=True)
class UpdateGroupActionResult:
    data: GroupData | None
