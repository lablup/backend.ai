"""Operation scopes for the links between projects and container registries."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.models.association_container_registries_groups.row import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.scopes import ExistenceCheck, ScopeTarget

__all__ = ("ProjectContainerRegistryAssociationTarget",)


@dataclass(frozen=True)
class ProjectContainerRegistryAssociationTarget(ScopeTarget):
    """The links of one project to the container registries it is allowed on."""

    project_id: ProjectID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.project_id

    @override
    def to_condition(self) -> QueryCondition:
        return lambda: AssociationContainerRegistriesGroupsRow.project_id == self.project_id

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return [
            ExistenceCheck(
                column=ProjectRow.id,
                value=self.project_id,
                error=ProjectNotFound(str(self.project_id)),
            ),
        ]
