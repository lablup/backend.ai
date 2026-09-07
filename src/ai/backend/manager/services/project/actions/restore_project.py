from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import RestoreSingleEntityOpsAction
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.project.updaters import ProjectRestoreUpdater


@dataclass(frozen=True)
class RestoreProjectAction(RestoreSingleEntityOpsAction[ProjectRow, ProjectData]):
    """Put one retired project back in service."""

    updater: ProjectRestoreUpdater

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.project_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "restore_project"

    @override
    def to_updater(self) -> ProjectRestoreUpdater:
        return self.updater
