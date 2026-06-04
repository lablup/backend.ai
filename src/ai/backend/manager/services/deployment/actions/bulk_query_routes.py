from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType, RBACElementType, ScopeType
from ai.backend.manager.actions.action.scope import BaseScopeAction, BaseScopeActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import ModelReplicaData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.repositories.base import Querier
from ai.backend.manager.repositories.deployment.types import UserRouteSearchScope


@dataclass
class BulkQueryRoutesAction(BaseScopeAction):
    """Resolve many routes (replicas) at once via independent by-key queriers,
    constrained to the requester's USER scope (routes they own)."""

    queriers: Sequence[Querier[RoutingRow]]
    scope: UserRouteSearchScope

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.DEPLOYMENT_REPLICA

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

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
class BulkQueryRoutesActionResult(BaseScopeActionResult):
    data: list[ModelReplicaData]
    _scope_id: str

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.USER

    @override
    def scope_id(self) -> str:
        return self._scope_id
