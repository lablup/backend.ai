from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.agent import (
    AgentResourceStatsResponse,
    GetAgentDetailResponse,
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

    async def get_agent(
        self,
        agent_id: str,
    ) -> GetAgentDetailResponse:
        return await self._client.typed_request(
            "GET",
            f"/agents/{agent_id}",
            response_model=GetAgentDetailResponse,
        )

    async def get_resource_stats(self) -> AgentResourceStatsResponse:
        return await self._client.typed_request(
            "GET",
            "/agents/resource-stats",
            response_model=AgentResourceStatsResponse,
        )
