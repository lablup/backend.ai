"""User search over the scopes users are reachable from."""

from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction, ScopeItem
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.user.scopes import (
    DomainUserTarget,
    ProjectUserTarget,
    RoleUserTarget,
)
from ai.backend.manager.models.user.searchers import UserSearcher

__all__ = (
    "DomainUserScopeItem",
    "ProjectUserScopeItem",
    "RoleUserScopeItem",
    "ScopedSearchUsersAction",
    "UserScopeItem",
)


class UserScopeItem(ScopeItem, ABC):
    """One side a user is reachable from."""


@dataclass(frozen=True)
class DomainUserScopeItem(UserScopeItem):
    """The users of one domain."""

    domain_id: DomainID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.domain_id

    @override
    def operation_scope(self) -> OperationScope:
        return DomainUserTarget(domain_id=self.domain_id)


@dataclass(frozen=True)
class ProjectUserScopeItem(UserScopeItem):
    """The users of one project."""

    project_id: ProjectID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.project_id

    @override
    def operation_scope(self) -> OperationScope:
        return ProjectUserTarget(project_id=self.project_id)


@dataclass(frozen=True)
class RoleUserScopeItem(UserScopeItem):
    """The users holding one role."""

    role_id: RoleID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.role_id

    @override
    def operation_scope(self) -> OperationScope:
        return RoleUserTarget(role_id=self.role_id)


@dataclass(frozen=True)
class ScopedSearchUsersAction(OperationScopeOpsAction[UserRow, UserData]):
    """Page through the users the named scopes reach, combined with OR.

    Every scope is authorized before the read runs, so a caller reaching for one they
    cannot see is refused rather than served the rest.
    """

    items: Sequence[UserScopeItem]
    searcher: UserSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return UserEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_users"

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [item.scope_id() for item in self.items]

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return [item.operation_scope() for item in self.items]

    @override
    def to_searcher(self) -> UserSearcher:
        return self.searcher
