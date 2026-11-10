from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.models.project.updaters import ProjectUpdater


@dataclass(frozen=True)
class UpdateProjectAction(BaseSingleEntityAction):
    """Edit one project. Who belongs to it is the roster's own operation."""

    updater: ProjectUpdater

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.project_id

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_project"


@dataclass(frozen=True)
class UpdateProjectActionResult:
    data: ProjectData | None
