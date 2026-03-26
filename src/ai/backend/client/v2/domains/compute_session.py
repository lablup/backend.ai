from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.compute_session import (
    GetComputeSessionDetailResponse,
    SearchComputeSessionsRequest,
    SearchComputeSessionsResponse,
)


class ComputeSessionClient(BaseDomainClient):
    """Client for compute session endpoints."""

    async def search_sessions(
        self,
        request: SearchComputeSessionsRequest,
    ) -> SearchComputeSessionsResponse:
        return await self._client.typed_request(
            "POST",
            "/compute-sessions/search",
            request=request,
            response_model=SearchComputeSessionsResponse,
        )

    async def get_session(
        self,
        session_id: str,
    ) -> GetComputeSessionDetailResponse:
        return await self._client.typed_request(
            "GET",
            f"/compute-sessions/{session_id}",
            response_model=GetComputeSessionDetailResponse,
        )
