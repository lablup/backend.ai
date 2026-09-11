"""Project search over the scopes projects are reachable from."""

from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.resource_group import (
    ResourceGroupID,
)
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction, ScopeItem
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.project.scopes import (
    DomainProjectOperationScope,
    ResourceGroupProjectOperationScope,
    UserProjectOperationScope,
)
from ai.backend.manager.models.project.searchers import ProjectSearcher
from ai.backend.manager.models.scopes import OperationScope

__all__ = (
    "DomainProjectScopeItem",
    "ProjectScopeItem",
    "ResourceGroupProjectScopeItem",
    "ScopedSearchProjectsAction",
    "UserProjectScopeItem",
)


class ProjectScopeItem(ScopeItem, ABC):
    """One side a project is reachable from."""


@dataclass(frozen=True)
class DomainProjectScopeItem(ProjectScopeItem):
    """The projects of one domain."""

    domain_id: DomainID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.domain_id

    @override
    def operation_scope(self) -> OperationScope:
        return DomainProjectOperationScope(domain_id=self.domain_id)


@dataclass(frozen=True)
class UserProjectScopeItem(ProjectScopeItem):
    """The projects one user belongs to."""

    user_id: UserID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.user_id

    @override
    def operation_scope(self) -> OperationScope:
        return UserProjectOperationScope(user_id=self.user_id)


@dataclass(frozen=True)
class ResourceGroupProjectScopeItem(ProjectScopeItem):
    """The projects one resource group serves."""

    resource_group_id: ResourceGroupID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.resource_group_id

    @override
    def operation_scope(self) -> OperationScope:
        return ResourceGroupProjectOperationScope(resource_group_id=self.resource_group_id)


@dataclass(frozen=True)
class ScopedSearchProjectsAction(OperationScopeOpsAction[ProjectRow, ProjectData]):
    """Page through the projects the named scopes reach, combined with OR.

    Every scope is authorized before the read runs, so a caller reaching for one they
    cannot see is refused rather than served the rest.
    """

    items: Sequence[ProjectScopeItem]
    searcher: ProjectSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ProjectEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_projects"

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [item.scope_id() for item in self.items]

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return [item.operation_scope() for item in self.items]

    @override
    def to_searcher(self) -> ProjectSearcher:
        return self.searcher
