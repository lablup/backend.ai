from __future__ import annotations

import pytest

from ai.backend.client.v2.exceptions import PermissionDeniedError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.scheduling_history import (
    DeploymentHistoryFilter,
    ListDeploymentHistoryResponse,
    ListRouteHistoryResponse,
    ListSessionHistoryResponse,
    RouteHistoryFilter,
    SchedulingResultType,
    SearchDeploymentHistoryRequest,
    SearchRouteHistoryRequest,
    SearchSessionHistoryRequest,
    SessionHistoryFilter,
)


class TestSessionSchedulingHistory:
    @pytest.mark.asyncio
    async def test_admin_searches_session_history(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Admin can search session scheduling history; response shape is valid even if empty."""
        result = await admin_registry.scheduling_history.search_session_history(
            SearchSessionHistoryRequest()
        )
        assert isinstance(result, ListSessionHistoryResponse)
        assert isinstance(result.items, list)
        assert result.pagination.total >= 0
        assert result.pagination.offset == 0

    @pytest.mark.asyncio
    async def test_search_session_history_with_pagination(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Pagination parameters are honoured by the session history endpoint."""
        result = await admin_registry.scheduling_history.search_session_history(
            SearchSessionHistoryRequest(limit=10, offset=0)
        )
        assert isinstance(result, ListSessionHistoryResponse)
        assert result.pagination.limit == 10
        assert result.pagination.offset == 0
        assert len(result.items) <= 10

    @pytest.mark.asyncio
    async def test_search_session_history_with_filters(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Filter by result type returns a valid (possibly empty) response."""
        result = await admin_registry.scheduling_history.search_session_history(
            SearchSessionHistoryRequest(
                filter=SessionHistoryFilter(
                    result=[SchedulingResultType.SUCCESS],
                )
            )
        )
        assert isinstance(result, ListSessionHistoryResponse)
        assert isinstance(result.items, list)
        # All returned items must match the requested filter
        for item in result.items:
            assert item.result == SchedulingResultType.SUCCESS

    @pytest.mark.asyncio
    async def test_regular_user_cannot_search_session_history(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """Regular user is forbidden from searching session scheduling history."""
        with pytest.raises(PermissionDeniedError):
            await user_registry.scheduling_history.search_session_history(
                SearchSessionHistoryRequest()
            )


class TestDeploymentSchedulingHistory:
    @pytest.mark.asyncio
    async def test_admin_searches_deployment_history(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Admin can search deployment scheduling history; response shape is valid even if empty."""
        result = await admin_registry.scheduling_history.search_deployment_history(
            SearchDeploymentHistoryRequest()
        )
        assert isinstance(result, ListDeploymentHistoryResponse)
        assert isinstance(result.items, list)
        assert result.pagination.total >= 0
        assert result.pagination.offset == 0

    @pytest.mark.asyncio
    async def test_search_deployment_history_with_pagination(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Pagination parameters are honoured by the deployment history endpoint."""
        result = await admin_registry.scheduling_history.search_deployment_history(
            SearchDeploymentHistoryRequest(limit=5, offset=0)
        )
        assert isinstance(result, ListDeploymentHistoryResponse)
        assert result.pagination.limit == 5
        assert result.pagination.offset == 0
        assert len(result.items) <= 5

    @pytest.mark.asyncio
    async def test_search_deployment_history_with_filters(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Filter by result type returns a valid (possibly empty) response."""
        result = await admin_registry.scheduling_history.search_deployment_history(
            SearchDeploymentHistoryRequest(
                filter=DeploymentHistoryFilter(
                    result=[SchedulingResultType.FAILURE],
                )
            )
        )
        assert isinstance(result, ListDeploymentHistoryResponse)
        assert isinstance(result.items, list)
        for item in result.items:
            assert item.result == SchedulingResultType.FAILURE

    @pytest.mark.asyncio
    async def test_regular_user_cannot_search_deployment_history(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """Regular user is forbidden from searching deployment scheduling history."""
        with pytest.raises(PermissionDeniedError):
            await user_registry.scheduling_history.search_deployment_history(
                SearchDeploymentHistoryRequest()
            )


class TestRouteSchedulingHistory:
    @pytest.mark.asyncio
    async def test_admin_searches_route_history(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Admin can search route scheduling history; response shape is valid even if empty."""
        result = await admin_registry.scheduling_history.search_route_history(
            SearchRouteHistoryRequest()
        )
        assert isinstance(result, ListRouteHistoryResponse)
        assert isinstance(result.items, list)
        assert result.pagination.total >= 0
        assert result.pagination.offset == 0

    @pytest.mark.asyncio
    async def test_search_route_history_with_pagination(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Pagination parameters are honoured by the route history endpoint."""
        result = await admin_registry.scheduling_history.search_route_history(
            SearchRouteHistoryRequest(limit=20, offset=0)
        )
        assert isinstance(result, ListRouteHistoryResponse)
        assert result.pagination.limit == 20
        assert result.pagination.offset == 0
        assert len(result.items) <= 20

    @pytest.mark.asyncio
    async def test_search_route_history_with_filters(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Filter by result type returns a valid (possibly empty) response."""
        result = await admin_registry.scheduling_history.search_route_history(
            SearchRouteHistoryRequest(
                filter=RouteHistoryFilter(
                    result=[SchedulingResultType.SUCCESS],
                )
            )
        )
        assert isinstance(result, ListRouteHistoryResponse)
        assert isinstance(result.items, list)
        for item in result.items:
            assert item.result == SchedulingResultType.SUCCESS

    @pytest.mark.asyncio
    async def test_regular_user_cannot_search_route_history(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """Regular user is forbidden from searching route scheduling history."""
        with pytest.raises(PermissionDeniedError):
            await user_registry.scheduling_history.search_route_history(SearchRouteHistoryRequest())
