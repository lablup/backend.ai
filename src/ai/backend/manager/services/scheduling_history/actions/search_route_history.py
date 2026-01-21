from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.deployment.types import RouteHistoryData
from ai.backend.manager.repositories.base import BatchQuerier

from .base import SchedulingHistoryAction


@dataclass
class SearchRouteHistoryAction(SchedulingHistoryAction):
    """Action to search route history."""

    querier: BatchQuerier

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "route:history"

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search"

    @override
    def entity_id(self) -> Optional[str]:
        return None


@dataclass
class SearchRouteHistoryActionResult(BaseActionResult):
    """Result of searching route history."""

    histories: list[RouteHistoryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None
