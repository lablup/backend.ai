from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import DeletePartialBulkOpsAction
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.project.updaters import ProjectSoftDeleteUpdater


@dataclass(frozen=True)
class PartialBulkDeleteProjectsAction(DeletePartialBulkOpsAction[ProjectRow, ProjectData]):
    """Retire the named projects, answering for each one."""

    ids: Sequence[ProjectID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_delete_projects"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_updaters(self) -> Mapping[EntityIdentifier, ProjectSoftDeleteUpdater]:
        return {
            project_id: ProjectSoftDeleteUpdater(project_id=project_id) for project_id in self.ids
        }

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[project_id for project_id in self.ids if project_id in allowed])
