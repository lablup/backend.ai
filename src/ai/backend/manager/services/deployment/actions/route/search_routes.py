"""Action for searching routes of a deployment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.deployment.types import (
    RouteInfo,
)
from ai.backend.manager.repositories.base import BatchQuerier

from .base import RouteBaseAction


@dataclass
class SearchRoutesAction(RouteBaseAction):
    """Action to search routes with filtering and pagination."""

    querier: BatchQuerier

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search_routes"


@dataclass
class SearchRoutesActionResult(BaseActionResult):
    """Result of searching routes."""

    routes: list[RouteInfo]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None
