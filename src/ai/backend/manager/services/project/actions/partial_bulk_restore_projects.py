from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import RestorePartialBulkOpsAction
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.project.updaters import ProjectRestoreUpdater


@dataclass(frozen=True)
class PartialBulkRestoreProjectsAction(RestorePartialBulkOpsAction[ProjectRow, ProjectData]):
    """Put the named retired projects back in service, answering for each one."""

    ids: Sequence[ProjectID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_restore_projects"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_updaters(self) -> Mapping[EntityIdentifier, ProjectRestoreUpdater]:
        return {project_id: ProjectRestoreUpdater(project_id=project_id) for project_id in self.ids}

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[project_id for project_id in self.ids if project_id in allowed])
