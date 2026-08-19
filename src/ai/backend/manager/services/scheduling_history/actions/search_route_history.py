from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment import DEPLOYMENT_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import RouteHistoryData
from ai.backend.manager.repositories.base import BatchQuerier

from .base import SchedulingHistoryAction


@dataclass
class SearchRouteHistoryAction(SchedulingHistoryAction):
    """Action to search route history (admin API)."""

    querier: BatchQuerier

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DEPLOYMENT_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_route_history"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchRouteHistoryActionResult:
    """Result of searching route history."""

    histories: list[RouteHistoryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
