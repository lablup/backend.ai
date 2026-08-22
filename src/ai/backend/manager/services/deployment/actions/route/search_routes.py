"""Action for searching routes of a deployment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import (
    RouteInfo,
)
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.deployment.actions.base import DeploymentGlobalAction


@dataclass
class SearchRoutesAction(DeploymentGlobalAction):
    """Action to search routes with filtering and pagination."""

    querier: BatchQuerier

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_routes"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchRoutesActionResult:
    """Result of searching routes."""

    routes: list[RouteInfo]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
