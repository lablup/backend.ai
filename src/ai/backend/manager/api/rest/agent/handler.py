"""Agent handler class using constructor dependency injection."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Final

from ai.backend.common.api_handlers import APIResponse, BodyParam
from ai.backend.common.dto.manager.agent.request import SearchAgentsRequest
from ai.backend.common.dto.manager.agent.response import PaginationInfo, SearchAgentsResponse
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.dto.context import UserContext
from ai.backend.manager.services.agent.actions.search_agents import SearchAgentsAction
from ai.backend.manager.services.processors import Processors

from .adapter import AgentAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AgentHandler:
    """Agent API handler with constructor-injected dependencies."""

    def __init__(self, *, processors: Processors) -> None:
        self._processors = processors
        self._adapter = AgentAdapter()

    async def search_agents(
        self,
        body: BodyParam[SearchAgentsRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Search agents with filters, orders, and pagination."""
        log.info("SEARCH_AGENTS (ak:{})", ctx.access_key)

        querier = self._adapter.build_querier(body.parsed)

        action_result = await self._processors.agent.search_agents.wait_for_complete(
            SearchAgentsAction(querier=querier)
        )

        resp = SearchAgentsResponse(
            items=[self._adapter.convert_to_dto(agent) for agent in action_result.agents],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)
