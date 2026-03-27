"""V2 REST SDK client for the agent resource."""

from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.agent.request import (
    AdminSearchAgentsInput,
)
from ai.backend.common.dto.manager.v2.agent.response import (
    AdminSearchAgentsPayload,
    AgentResourceStatsPayload,
)

_PATH = "/v2/agents"


class V2AgentClient(BaseDomainClient):
    """SDK client for ``/v2/agents`` endpoints."""

    async def admin_search(
        self,
        request: AdminSearchAgentsInput,
    ) -> AdminSearchAgentsPayload:
        """Search agents with filters, orders, and pagination (superadmin only)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=AdminSearchAgentsPayload,
        )

    async def get_total_resources(self) -> AgentResourceStatsPayload:
        """Get aggregate resource statistics across all agents (superadmin only)."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/total-resources",
            response_model=AgentResourceStatsPayload,
        )
