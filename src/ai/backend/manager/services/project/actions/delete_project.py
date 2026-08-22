from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import DeleteSingleEntityOpsAction
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.project.updaters import ProjectSoftDeleteUpdater


@dataclass(frozen=True)
class DeleteProjectAction(DeleteSingleEntityOpsAction[ProjectRow, ProjectData]):
    """Retire one project."""

    updater: ProjectSoftDeleteUpdater

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.project_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_project"

    @override
    def to_updater(self) -> ProjectSoftDeleteUpdater:
        return self.updater
