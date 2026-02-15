"""
REST API handler for Agent resources.
Provides search, detail, and resource stats endpoints for agents.
"""

from __future__ import annotations

from collections.abc import Iterable
from http import HTTPStatus

import aiohttp_cors
from aiohttp import web

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam, api_handler
from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.agent.request import AgentPathParam, SearchAgentsRequest
from ai.backend.common.dto.manager.agent.response import (
    AgentResourceStatsResponse,
    GetAgentDetailResponse,
    PaginationInfo,
    SearchAgentsResponse,
)
from ai.backend.common.types import AgentId
from ai.backend.manager.api.auth import auth_required_for_method
from ai.backend.manager.api.types import CORSOptions, WebMiddleware
from ai.backend.manager.dto.context import ProcessorsCtx
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.services.agent.actions.get_agent import GetAgentAction
from ai.backend.manager.services.agent.actions.get_total_resources import GetTotalResourcesAction
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

    @auth_required_for_method
    @api_handler
    async def get_agent_detail(
        self,
        path: PathParam[AgentPathParam],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Get a single agent detail by ID."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise NotEnoughPermission("Only superadmin can get agent details.")

        action_result = await processors.agent.get_agent.wait_for_complete(
            GetAgentAction(agent_id=AgentId(path.parsed.agent_id))
        )

        resp = GetAgentDetailResponse(
            agent=self.agent_adapter.convert_to_dto(action_result.data),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def get_resource_stats(
        self,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Get aggregate resource stats across all agents."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise NotEnoughPermission("Only superadmin can get resource stats.")

        action_result = await processors.agent.get_total_resources.wait_for_complete(
            GetTotalResourcesAction()
        )

        total = action_result.total_resources
        resp = AgentResourceStatsResponse(
            total_used_slots=dict(total.total_used_slots.to_json()),
            total_free_slots=dict(total.total_free_slots.to_json()),
            total_capacity_slots=dict(total.total_capacity_slots.to_json()),
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
    cors.add(app.router.add_route("GET", "/resource-stats", api_handler.get_resource_stats))
    cors.add(app.router.add_route("GET", "/{agent_id}", api_handler.get_agent_detail))

    return app, []
