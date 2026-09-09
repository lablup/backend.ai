"""Actions for reading projects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.v2.ops.base import (
    GetSingleEntityOpsAction,
    SearchGlobalOpsAction,
)
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.models.project.queriers import ProjectQuerier
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.project.searchers import ProjectSearcher


@dataclass(frozen=True)
class GlobalSearchProjectsAction(SearchGlobalOpsAction[ProjectRow, ProjectData]):
    """Page through every project in the installation."""

    searcher: ProjectSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ProjectEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_projects"

    @override
    def to_searcher(self) -> ProjectSearcher:
        return self.searcher


@dataclass(frozen=True)
class GetProjectAction(GetSingleEntityOpsAction[ProjectRow, ProjectData]):
    """Read one project by its id."""

    project_id: ProjectID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.project_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_project"

    @override
    def to_querier(self) -> ProjectQuerier:
        return ProjectQuerier(project_id=self.project_id)
