from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import RouteHistoryData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.scheduling_history.types import RouteHistorySearchScope

from .base import SchedulingHistoryAction


@dataclass
class SearchRouteScopedHistoryAction(SchedulingHistoryAction):
    """Action to search route history within a route scope.

    This is the scoped version used by entity-scoped APIs.
    Scope is required and specifies which route to query history for.
    """

    scope: RouteHistorySearchScope
    querier: BatchQuerier

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.ROUTE_SCOPED_HISTORY

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def entity_id(self) -> str | None:
        return str(self.scope.route_id)


@dataclass
class SearchRouteScopedHistoryActionResult(BaseActionResult):
    """Result of searching route history within scope."""

    histories: list[RouteHistoryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
