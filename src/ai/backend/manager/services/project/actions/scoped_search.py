"""Project search over the scopes projects are reachable from."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.domain import DOMAIN_SCOPE_TYPE, DomainID
from ai.backend.common.data.entity.project import PROJECT_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType, ScopeRef
from ai.backend.common.data.entity.user import USER_SCOPE_TYPE, UserID
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.project.scopes import (
    DomainProjectOperationScope,
    UserProjectOperationScope,
)
from ai.backend.manager.models.project.searchers import ProjectSearcher
from ai.backend.manager.models.scopes import OperationScope

__all__ = (
    "DomainProjectScopeItem",
    "ProjectScopeItem",
    "ScopedSearchProjectsAction",
    "UserProjectScopeItem",
)


class ProjectScopeItem(ABC):
    """One side a project is reachable from.

    The scope the read is answered for and the rows it is restricted to are declared
    together, so a read cannot be authorized against one thing and served another.
    """

    @abstractmethod
    def scope_ref(self) -> ScopeRef:
        """The scope the read is answered for."""
        raise NotImplementedError

    @abstractmethod
    def operation_scope(self) -> OperationScope:
        """The rows the read is restricted to."""
        raise NotImplementedError


@dataclass(frozen=True)
class DomainProjectScopeItem(ProjectScopeItem):
    """The projects of one domain."""

    domain_id: DomainID

    @override
    def scope_ref(self) -> ScopeRef:
        return ScopeRef(scope_type=DOMAIN_SCOPE_TYPE, scope_id=self.domain_id)

    @override
    def operation_scope(self) -> OperationScope:
        return DomainProjectOperationScope(domain_id=self.domain_id)


@dataclass(frozen=True)
class UserProjectScopeItem(ProjectScopeItem):
    """The projects one user belongs to."""

    user_id: UserID

    @override
    def scope_ref(self) -> ScopeRef:
        return ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=self.user_id)

    @override
    def operation_scope(self) -> OperationScope:
        return UserProjectOperationScope(user_id=self.user_id)


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
        return PROJECT_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_projects"

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return [item.scope_ref() for item in self.items]

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return [item.operation_scope() for item in self.items]

    @override
    def to_searcher(self) -> ProjectSearcher:
        return self.searcher
