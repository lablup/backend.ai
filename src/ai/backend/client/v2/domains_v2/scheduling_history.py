"""V2 SDK client for the scheduling history domain."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.scheduling_history.request import (
    AdminSearchDeploymentHistoriesInput,
    AdminSearchRouteHistoriesInput,
    AdminSearchSessionHistoriesInput,
)
from ai.backend.common.dto.manager.v2.scheduling_history.response import (
    AdminSearchDeploymentHistoriesPayload,
    AdminSearchRouteHistoriesPayload,
    AdminSearchSessionHistoriesPayload,
)

_PATH = "/v2/scheduling-history"


class V2SchedulingHistoryClient(BaseDomainClient):
    """SDK client for scheduling history operations."""

    # ========== Session History ==========

    async def search_session_history(
        self, request: AdminSearchSessionHistoriesInput
    ) -> AdminSearchSessionHistoriesPayload:
        """Search session scheduling histories with admin scope."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/sessions/search",
            request=request,
            response_model=AdminSearchSessionHistoriesPayload,
        )

    async def session_scoped_search(
        self, session_id: UUID, request: AdminSearchSessionHistoriesInput
    ) -> AdminSearchSessionHistoriesPayload:
        """Search session scheduling histories scoped to a specific session."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/sessions/{session_id}/search",
            request=request,
            response_model=AdminSearchSessionHistoriesPayload,
        )

    # ========== Deployment History ==========

    async def search_deployment_history(
        self, request: AdminSearchDeploymentHistoriesInput
    ) -> AdminSearchDeploymentHistoriesPayload:
        """Search deployment histories with admin scope."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/deployments/search",
            request=request,
            response_model=AdminSearchDeploymentHistoriesPayload,
        )

    async def deployment_scoped_search(
        self, deployment_id: UUID, request: AdminSearchDeploymentHistoriesInput
    ) -> AdminSearchDeploymentHistoriesPayload:
        """Search deployment histories scoped to a specific deployment."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/deployments/{deployment_id}/search",
            request=request,
            response_model=AdminSearchDeploymentHistoriesPayload,
        )

    # ========== Route History ==========

    async def search_route_history(
        self, request: AdminSearchRouteHistoriesInput
    ) -> AdminSearchRouteHistoriesPayload:
        """Search route histories with admin scope."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/routes/search",
            request=request,
            response_model=AdminSearchRouteHistoriesPayload,
        )

    async def route_scoped_search(
        self, route_id: UUID, request: AdminSearchRouteHistoriesInput
    ) -> AdminSearchRouteHistoriesPayload:
        """Search route histories scoped to a specific route."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/routes/{route_id}/search",
            request=request,
            response_model=AdminSearchRouteHistoriesPayload,
        )
