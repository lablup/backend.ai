from abc import ABC
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role import RoleEntityType
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.ops.base import ScopeItem
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.data.common.types import SearchResult
from ai.backend.manager.data.permission.role import RoleData
from ai.backend.manager.models.rbac_models.role.scopes import (
    HeldRoleTarget,
    ScopedRoleTarget,
)
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.repositories.base import BatchQuerier

__all__ = (
    "HolderRoleScopeItem",
    "RegisteredRoleScopeItem",
    "RoleScopeItem",
    "SearchRolesInScopeAction",
    "SearchRolesInScopeActionResult",
)


class RoleScopeItem(ScopeItem, ABC):
    """One side a role is reachable from."""


@dataclass(frozen=True)
class RegisteredRoleScopeItem(RoleScopeItem):
    """The roles registered in one scope."""

    scope: EntityIdentifier

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.scope

    @override
    def operation_scope(self) -> OperationScope:
        return ScopedRoleTarget(scope=self.scope)


@dataclass(frozen=True)
class HolderRoleScopeItem(RoleScopeItem):
    """The roles one user holds."""

    user_id: UserID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.user_id

    @override
    def operation_scope(self) -> OperationScope:
        return HeldRoleTarget(user_id=self.user_id)


@dataclass(frozen=True)
class SearchRolesInScopeAction(BaseScopeAction):
    """Read the roles the named scopes reach, combined with OR.

    A role created before the v2 write path has no virtual entity node yet and is
    absent from this answer until BA-7571 backfills one.
    """

    items: Sequence[RoleScopeItem]
    querier: BatchQuerier

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
        return "search_roles_in_scope"

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [item.scope_id() for item in self.items]

    def operation_scopes(self) -> Sequence[OperationScope]:
        return [item.operation_scope() for item in self.items]


@dataclass(frozen=True)
class SearchRolesInScopeActionResult(BaseScopeActionResult):
    result: SearchResult[RoleData]

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return [item.id for item in self.result.items]
