from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.scheduling_history import (
    ListDeploymentHistoryResponse,
    ListRouteHistoryResponse,
    ListSessionHistoryResponse,
    SearchDeploymentHistoryRequest,
    SearchRouteHistoryRequest,
    SearchSessionHistoryRequest,
)


class SchedulingHistoryClient(BaseDomainClient):
    """Client for scheduling history endpoints."""

    async def search_session_history(
        self,
        request: SearchSessionHistoryRequest,
    ) -> ListSessionHistoryResponse:
        return await self._client.typed_request(
            "POST",
            "/scheduling-history/sessions/search",
            request=request,
            response_model=ListSessionHistoryResponse,
        )

    async def search_deployment_history(
        self,
        request: SearchDeploymentHistoryRequest,
    ) -> ListDeploymentHistoryResponse:
        return await self._client.typed_request(
            "POST",
            "/scheduling-history/deployments/search",
            request=request,
            response_model=ListDeploymentHistoryResponse,
        )

    async def search_route_history(
        self,
        request: SearchRouteHistoryRequest,
    ) -> ListRouteHistoryResponse:
        return await self._client.typed_request(
            "POST",
            "/scheduling-history/routes/search",
            request=request,
            response_model=ListRouteHistoryResponse,
        )
