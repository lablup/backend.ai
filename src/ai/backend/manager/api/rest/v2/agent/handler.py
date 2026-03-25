"""REST v2 handler for the agent resource."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam
from ai.backend.common.dto.manager.v2.agent.request import AdminSearchAgentsInput
from ai.backend.common.dto.manager.v2.agent.response import AgentResourceStatsPayload
from ai.backend.logging import BraceStyleAdapter

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.agent import AgentAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2AgentHandler:
    """REST v2 handler for agent operations."""

    def __init__(self, *, adapter: AgentAdapter) -> None:
        self._adapter = adapter

    async def admin_search(
        self,
        body: BodyParam[AdminSearchAgentsInput],
    ) -> APIResponse:
        """Search agents with filters, orders, and pagination (superadmin only)."""
        result = await self._adapter.admin_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def get_total_resources(self) -> APIResponse:
        """Retrieve aggregate resource capacity/usage across all agents (superadmin only)."""
        data = await self._adapter.get_total_resources()
        payload = AgentResourceStatsPayload(
            total_used_slots=dict(data.total_used_slots.to_json()),
            total_free_slots=dict(data.total_free_slots.to_json()),
            total_capacity_slots=dict(data.total_capacity_slots.to_json()),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=payload)
