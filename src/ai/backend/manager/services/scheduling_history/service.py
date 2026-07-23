from __future__ import annotations

from ai.backend.manager.models.scopes import SearchScope
from ai.backend.manager.repositories.scheduling_history import SchedulingHistoryRepository
from ai.backend.manager.repositories.scheduling_history.types import (
    KernelSchedulingHistoryBySessionSearchScope,
    KernelSchedulingHistorySearchScope,
)

from .actions.resolve_kernel_session import (
    ResolveKernelSessionAction,
    ResolveKernelSessionActionResult,
)
from .actions.search_deployment_history import (
    SearchDeploymentHistoryAction,
    SearchDeploymentHistoryActionResult,
)
from .actions.search_deployment_scoped_history import (
    SearchDeploymentScopedHistoryAction,
    SearchDeploymentScopedHistoryActionResult,
)
from .actions.search_kernel_history import (
    SearchKernelHistoryAction,
    SearchKernelHistoryActionResult,
)
from .actions.search_kernel_scoped_history import (
    SearchKernelScopedHistoryAction,
    SearchKernelScopedHistoryActionResult,
)
from .actions.search_route_history import (
    SearchRouteHistoryAction,
    SearchRouteHistoryActionResult,
)
from .actions.search_route_scoped_history import (
    SearchRouteScopedHistoryAction,
    SearchRouteScopedHistoryActionResult,
)
from .actions.search_session_history import (
    SearchSessionHistoryAction,
    SearchSessionHistoryActionResult,
)
from .actions.search_session_scoped_history import (
    SearchSessionScopedHistoryAction,
    SearchSessionScopedHistoryActionResult,
)


class SchedulingHistoryService:
    """Service for scheduling history operations."""

    _repository: SchedulingHistoryRepository

    def __init__(self, repository: SchedulingHistoryRepository) -> None:
        self._repository = repository

    # Admin methods (no scope)

    async def search_session_history(
        self,
        action: SearchSessionHistoryAction,
    ) -> SearchSessionHistoryActionResult:
        """Searches session scheduling history (admin API)."""
        result = await self._repository.search_session_history(
            querier=action.querier,
        )

        return SearchSessionHistoryActionResult(
            histories=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def search_kernel_history(
        self,
        action: SearchKernelHistoryAction,
    ) -> SearchKernelHistoryActionResult:
        """Searches kernel scheduling history (admin API)."""
        result = await self._repository.search_kernel_history(
            querier=action.querier,
        )

        return SearchKernelHistoryActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def search_deployment_history(
        self,
        action: SearchDeploymentHistoryAction,
    ) -> SearchDeploymentHistoryActionResult:
        """Searches deployment history (admin API)."""
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
        """Searches route history (admin API)."""
        result = await self._repository.search_route_history(
            querier=action.querier,
        )

        return SearchRouteHistoryActionResult(
            histories=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    # Scoped methods (added in 26.2.0)

    async def search_session_scoped_history(
        self,
        action: SearchSessionScopedHistoryAction,
    ) -> SearchSessionScopedHistoryActionResult:
        """Searches session scheduling history within scope."""
        result = await self._repository.search_session_scoped_history(
            querier=action.querier,
            scope=action.scope,
        )

        return SearchSessionScopedHistoryActionResult(
            histories=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def resolve_kernel_session(
        self,
        action: ResolveKernelSessionAction,
    ) -> ResolveKernelSessionActionResult:
        """Resolves the session owning a kernel; raises KernelNotFound if absent."""
        session_id = await self._repository.resolve_session_id(action.kernel_id)
        return ResolveKernelSessionActionResult(session_id=session_id)

    async def search_kernel_scoped_history(
        self,
        action: SearchKernelScopedHistoryAction,
    ) -> SearchKernelScopedHistoryActionResult:
        """Searches kernel scheduling history within the caller's authorized scopes."""
        scope: SearchScope
        if action.kernel_id is not None:
            scope = KernelSchedulingHistorySearchScope(kernel_id=action.kernel_id)
        else:
            scope = KernelSchedulingHistoryBySessionSearchScope(session_id=action.session_id)
        result = await self._repository.search_kernel_scoped_history(
            querier=action.querier,
            scopes=[scope],
        )

        return SearchKernelScopedHistoryActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            kernel_id=action.kernel_id,
            session_id=action.session_id,
        )

    async def search_deployment_scoped_history(
        self,
        action: SearchDeploymentScopedHistoryAction,
    ) -> SearchDeploymentScopedHistoryActionResult:
        """Searches deployment history within scope."""
        result = await self._repository.search_deployment_scoped_history(
            querier=action.querier,
            scope=action.scope,
        )

        return SearchDeploymentScopedHistoryActionResult(
            histories=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def search_route_scoped_history(
        self,
        action: SearchRouteScopedHistoryAction,
    ) -> SearchRouteScopedHistoryActionResult:
        """Searches route history within scope."""
        result = await self._repository.search_route_scoped_history(
            querier=action.querier,
            scope=action.scope,
        )

        return SearchRouteScopedHistoryActionResult(
            histories=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )
