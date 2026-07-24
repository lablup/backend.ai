from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType, RBACElementType, ScopeType
from ai.backend.common.identifier.replica import ReplicaID
from ai.backend.manager.actions.action.scope import BaseScopeAction, BaseScopeActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import RouteHistoryData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.base import BatchQuerier


@dataclass
class SearchRouteScopedHistoryAction(BaseScopeAction):
    """Action to search the scheduling history of one route.

    The history is the entity being read and the route is the scope containing it,
    so the RBAC scope chain authorizes the caller for reading history there.
    """

    route_id: ReplicaID
    querier: BatchQuerier

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.ROUTE_HISTORY

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.ROUTING

    @override
    def scope_id(self) -> str:
        return str(self.route_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.ROUTING,
            element_id=str(self.route_id),
        )


@dataclass
class SearchRouteScopedHistoryActionResult(BaseScopeActionResult):
    """Result of searching the scheduling history of one route."""

    histories: list[RouteHistoryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
    route_id: ReplicaID

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.ROUTING

    @override
    def scope_id(self) -> str:
        return str(self.route_id)
