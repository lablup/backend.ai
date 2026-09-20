from collections.abc import Sequence
from dataclasses import dataclass
from typing import final, override

from ai.backend.common.data.entity.role import RoleEntityType
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.data.common.types import SearchResult
from ai.backend.manager.data.permission.role import RoleData
from ai.backend.manager.models.rbac_models.role.scopes import RoleTarget
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.repositories.base import BatchQuerier

__all__ = (
    "SearchRolesInScopeAction",
    "SearchRolesInScopeActionResult",
)


@dataclass(frozen=True)
class SearchRolesInScopeAction(BaseScopeAction):
    """Read the roles the named scopes reach, combined with OR.

    A role created before the v2 write path has no virtual entity node yet and is
    absent from this answer until BA-7571 backfills one.
    """

    targets: Sequence[RoleTarget]
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

    @final
    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [target.scope_id() for target in self.targets]

    @final
    def operation_scopes(self) -> Sequence[OperationScope]:
        return self.targets


@dataclass(frozen=True)
class SearchRolesInScopeActionResult(BaseScopeActionResult):
    result: SearchResult[RoleData]

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return [item.id for item in self.result.items]
