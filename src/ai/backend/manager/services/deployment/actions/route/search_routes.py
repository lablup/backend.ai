"""Action for searching routes of a deployment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
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
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchRoutesActionResult(BaseActionResult):
    """Result of searching routes."""

    routes: list[RouteInfo]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
