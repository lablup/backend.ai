"""Project search over the scopes projects are reachable from."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import final, override

from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.project.scopes import ProjectTarget
from ai.backend.manager.models.project.searchers import ProjectSearcher
from ai.backend.manager.models.scopes import OperationScope

__all__ = ("ScopedSearchProjectsAction",)


@dataclass(frozen=True)
class ScopedSearchProjectsAction(OperationScopeOpsAction[ProjectRow, ProjectData]):
    """Page through the projects the named scopes reach, combined with OR.

    Every scope is authorized before the read runs, so a caller reaching for one they
    cannot see is refused rather than served the rest.
    """

    targets: Sequence[ProjectTarget]
    searcher: ProjectSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ProjectEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_projects"

    @final
    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [target.scope_id() for target in self.targets]

    @final
    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return self.targets

    @override
    def to_searcher(self) -> ProjectSearcher:
        return self.searcher
