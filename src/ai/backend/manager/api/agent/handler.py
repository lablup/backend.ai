"""
REST API handler for Agent resources.
Provides a search endpoint for listing agents with filters and pagination.
"""

from __future__ import annotations

from collections.abc import Iterable
from http import HTTPStatus

import aiohttp_cors
from aiohttp import web

from ai.backend.common.api_handlers import APIResponse, BodyParam, api_handler
from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.agent.request import SearchAgentsRequest
from ai.backend.common.dto.manager.agent.response import PaginationInfo, SearchAgentsResponse
from ai.backend.manager.api.auth import auth_required_for_method
from ai.backend.manager.api.types import CORSOptions, WebMiddleware
from ai.backend.manager.dto.context import ProcessorsCtx
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.services.agent.actions.search_agents import SearchAgentsAction

from .agent_adapter import AgentAdapter


class AgentAPIHandler:
    """REST API handler for agent operations."""

    def __init__(self) -> None:
        self.agent_adapter = AgentAdapter()

    @auth_required_for_method
    @api_handler
    async def search_agents(
        self,
        body: BodyParam[SearchAgentsRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Search agents with filters, orders, and pagination."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise NotEnoughPermission("Only superadmin can list agents.")

        querier = self.agent_adapter.build_querier(body.parsed)

        action_result = await processors.agent.search_agents.wait_for_complete(
            SearchAgentsAction(querier=querier)
        )

        resp = SearchAgentsResponse(
            items=[self.agent_adapter.convert_to_dto(agent) for agent in action_result.agents],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    """Create aiohttp application for Agent API endpoints."""
    app = web.Application()
    app["api_versions"] = (4, 5)
    app["prefix"] = "agents"

    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    api_handler = AgentAPIHandler()

    cors.add(app.router.add_route("POST", "/search", api_handler.search_agents))

    return app, []
