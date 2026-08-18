"""Actions for reading projects."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.domain import DOMAIN_SCOPE_TYPE, DomainID
from ai.backend.common.data.entity.project import PROJECT_ENTITY_TYPE, ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, ScopeRef
from ai.backend.common.data.entity.user import USER_SCOPE_TYPE, UserID
from ai.backend.manager.actions.v2.ops.base import (
    GetSingleEntityOpsAction,
    OperationScopeOpsAction,
    SearchGlobalOpsAction,
)
from ai.backend.manager.data.group.types import GroupData
from ai.backend.manager.models.group.queriers import GroupQuerier
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.models.group.searchers import GroupSearcher
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.repositories.group.types import (
    DomainProjectOperationScope,
    UserProjectOperationScope,
)


@dataclass(frozen=True)
class GlobalSearchProjectsAction(SearchGlobalOpsAction[GroupRow, GroupData]):
    """Page through every project in the installation."""

    searcher: GroupSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return PROJECT_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_projects"

    @override
    def to_searcher(self) -> GroupSearcher:
        return self.searcher


@dataclass(frozen=True)
class SearchProjectsByDomainAction(OperationScopeOpsAction[GroupRow, GroupData]):
    """Page through the projects of a domain."""

    domain_id: DomainID
    searcher: GroupSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return PROJECT_ENTITY_TYPE

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=DOMAIN_SCOPE_TYPE, scope_id=self.domain_id),)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return (DomainProjectOperationScope(domain_id=self.domain_id),)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_projects_by_domain"

    @override
    def to_searcher(self) -> GroupSearcher:
        return self.searcher


@dataclass(frozen=True)
class SearchProjectsByUserAction(OperationScopeOpsAction[GroupRow, GroupData]):
    """Page through the projects a user belongs to."""

    user_id: UserID
    searcher: GroupSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return PROJECT_ENTITY_TYPE

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=self.user_id),)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return (UserProjectOperationScope(user_uuid=self.user_id),)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_projects_by_user"

    @override
    def to_searcher(self) -> GroupSearcher:
        return self.searcher


@dataclass(frozen=True)
class GetProjectAction(GetSingleEntityOpsAction[GroupRow, GroupData]):
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
    def to_querier(self) -> GroupQuerier:
        return GroupQuerier(project_id=self.project_id)
