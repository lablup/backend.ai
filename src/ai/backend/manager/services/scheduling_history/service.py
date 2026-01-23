from __future__ import annotations

from ai.backend.manager.repositories.scheduling_history import SchedulingHistoryRepository

from .actions.search_deployment_history import (
    SearchDeploymentHistoryAction,
    SearchDeploymentHistoryActionResult,
)
from .actions.search_route_history import (
    SearchRouteHistoryAction,
    SearchRouteHistoryActionResult,
)
from .actions.search_session_history import (
    SearchSessionHistoryAction,
    SearchSessionHistoryActionResult,
)


class SchedulingHistoryService:
    """Service for scheduling history operations."""

    _repository: SchedulingHistoryRepository

    def __init__(self, repository: SchedulingHistoryRepository) -> None:
        self._repository = repository

    async def search_session_history(
        self,
        action: SearchSessionHistoryAction,
    ) -> SearchSessionHistoryActionResult:
        """Searches session scheduling history."""
        result = await self._repository.search_session_history(
            querier=action.querier,
        )

        return SearchSessionHistoryActionResult(
            histories=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def search_deployment_history(
        self,
        action: SearchDeploymentHistoryAction,
    ) -> SearchDeploymentHistoryActionResult:
        """Searches deployment history."""
        result = await self._repository.search_deployment_history(
            querier=action.querier,
        )

        return SearchDeploymentHistoryActionResult(
            histories=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def search_route_history(
        self,
        action: SearchRouteHistoryAction,
    ) -> SearchRouteHistoryActionResult:
        """Searches route history."""
        result = await self._repository.search_route_history(
            querier=action.querier,
        )

        return SearchRouteHistoryActionResult(
            histories=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )
