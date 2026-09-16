from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role import RoleEntityType, RoleID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.ops.base import ScopeItem
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.data.common.types import SearchResult
from ai.backend.manager.data.permission.role import AssignedUserData
from ai.backend.manager.models.rbac_models.user_role.scopes import (
    RoleRoleAssignmentOperationScope,
    UserRoleAssignmentOperationScope,
)
from ai.backend.manager.models.rbac_models.user_role.searchers import RoleAssignmentSearcher
from ai.backend.manager.models.scopes import OperationScope

__all__ = (
    "RoleAssignmentScopeItem",
    "RoleRoleAssignmentScopeItem",
    "ScopedSearchRoleAssignmentsAction",
    "ScopedSearchRoleAssignmentsActionResult",
    "UserRoleAssignmentScopeItem",
)


class RoleAssignmentScopeItem(ScopeItem, ABC):
    """One side an assignment row is reachable from."""


@dataclass(frozen=True)
class UserRoleAssignmentScopeItem(RoleAssignmentScopeItem):
    """The assignment rows of the roles one user holds."""

    user_id: UserID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.user_id

    @override
    def operation_scope(self) -> OperationScope:
        return UserRoleAssignmentOperationScope(user_id=self.user_id)


@dataclass(frozen=True)
class RoleRoleAssignmentScopeItem(RoleAssignmentScopeItem):
    """The assignment rows of the users holding one role."""

    role_id: RoleID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.role_id

    @override
    def operation_scope(self) -> OperationScope:
        return RoleRoleAssignmentOperationScope(role_id=self.role_id)


@dataclass(frozen=True)
class ScopedSearchRoleAssignmentsAction(BaseScopeAction):
    """Read the assignment rows the named scopes reach, combined with OR.

    The rows join a user to a role and belong to neither, so the read is answered for
    by the scopes it stays inside rather than by a row of its own.
    """

    items: Sequence[RoleAssignmentScopeItem]
    searcher: RoleAssignmentSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RoleEntityType()

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_role_assignments"

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [item.scope_id() for item in self.items]

    def operation_scopes(self) -> Sequence[OperationScope]:
        return [item.operation_scope() for item in self.items]


@dataclass(frozen=True)
class ScopedSearchRoleAssignmentsActionResult(BaseScopeActionResult):
    result: SearchResult[AssignedUserData]

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return []
