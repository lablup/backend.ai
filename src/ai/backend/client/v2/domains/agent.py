from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.agent import (
    SearchAgentsRequest,
    SearchAgentsResponse,
)


class AgentClient(BaseDomainClient):
    """Client for agent management endpoints."""

    async def search_agents(
        self,
        request: SearchAgentsRequest,
    ) -> SearchAgentsResponse:
        return await self._client.typed_request(
            "POST",
            "/agents/search",
            request=request,
            response_model=SearchAgentsResponse,
        )
