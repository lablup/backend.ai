"""Actions for searching projects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.group.types import GroupData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.base.querier import BatchQuerier
from ai.backend.manager.repositories.group.types import (
    DomainProjectSearchScope,
    UserProjectSearchScope,
)
from ai.backend.manager.services.group.actions.base import (
    GroupAction,
    GroupScopeAction,
    GroupScopeActionResult,
    GroupSingleEntityAction,
    GroupSingleEntityActionResult,
)


@dataclass
class SearchProjectsAction(GroupAction):
    """Search all projects (admin scope - no scope filter)."""

    querier: BatchQuerier

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchProjectsByDomainAction(GroupScopeAction):
    """Search projects within a domain."""

    scope: DomainProjectSearchScope
    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.DOMAIN

    @override
    def scope_id(self) -> str:
        return self.scope.domain_name

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.DOMAIN, self.scope.domain_name)


@dataclass
class SearchProjectsByUserAction(GroupScopeAction):
    """Search projects a user is member of."""

    scope: UserProjectSearchScope
    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.USER

    @override
    def scope_id(self) -> str:
        return str(self.scope.user_uuid)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.USER, str(self.scope.user_uuid))


@dataclass
class GetProjectAction(GroupSingleEntityAction):
    """Get a single project by UUID."""

    project_id: UUID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def target_entity_id(self) -> str:
        return str(self.project_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.PROJECT, str(self.project_id))


# Result types


@dataclass
class SearchProjectsActionResult(BaseActionResult):
    """Result from searching projects (admin scope)."""

    items: list[GroupData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class ScopedSearchProjectsActionResult(GroupScopeActionResult):
    """Result from searching projects within a scope."""

    items: list[GroupData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
    _scope_type: ScopeType
    _scope_id: str

    @override
    def scope_type(self) -> ScopeType:
        return self._scope_type

    @override
    def scope_id(self) -> str:
        return self._scope_id


@dataclass
class GetProjectActionResult(GroupSingleEntityActionResult):
    """Result from getting a single project."""

    data: GroupData

    @override
    def target_entity_id(self) -> str:
        return str(self.data.id)
