from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import final, override

from ai.backend.common.data.entity.deployment import DeploymentEntityType
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.data.deployment.types import RouteHistoryData
from ai.backend.manager.models.scheduling_history.scopes import RouteHistoryTarget
from ai.backend.manager.models.scheduling_history.searchers import RouteHistorySearcher

from .base import SchedulingHistoryScopeActionResult


@dataclass
class SearchRouteScopedHistoryAction(BaseScopeAction):
    """Action to search route history within a route scope.

    The scope names the replica the rows are narrowed to and the deployment that owns it,
    which is what the read is answered for.
    """

    scope: RouteHistoryTarget
    searcher: RouteHistorySearcher

    @final
    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return (self.scope.scope_id(),)

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DeploymentEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_route_scoped_history"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchRouteScopedHistoryActionResult(SchedulingHistoryScopeActionResult):
    """Result of searching route history within scope."""

    histories: list[RouteHistoryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
