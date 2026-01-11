"""
REST API handlers for scheduling history.
Provides search endpoints for session, deployment, and route scheduling history.
"""

from __future__ import annotations

from collections.abc import Iterable
from http import HTTPStatus

import aiohttp_cors
from aiohttp import web

from ai.backend.common.api_handlers import APIResponse, BodyParam, api_handler
from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.scheduling_history import (
    ListDeploymentHistoryResponse,
    ListRouteHistoryResponse,
    ListSessionHistoryResponse,
    PaginationInfo,
    SearchDeploymentHistoryRequest,
    SearchRouteHistoryRequest,
    SearchSessionHistoryRequest,
)
from ai.backend.manager.api.auth import auth_required_for_method
from ai.backend.manager.api.types import CORSOptions, WebMiddleware
from ai.backend.manager.dto.context import ProcessorsCtx
from ai.backend.manager.services.scheduling_history.actions import (
    SearchDeploymentHistoryAction,
    SearchRouteHistoryAction,
    SearchSessionHistoryAction,
)

from .adapter import SchedulingHistoryAdapter

__all__ = ("create_app",)


class SchedulingHistoryAPIHandler:
    """REST API handler class for scheduling history operations."""

    def __init__(self) -> None:
        self._adapter = SchedulingHistoryAdapter()

    @auth_required_for_method
    @api_handler
    async def search_session_history(
        self,
        body: BodyParam[SearchSessionHistoryRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Search session scheduling history."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can search scheduling history.")

        querier = self._adapter.build_session_history_querier(body.parsed)

        action_result = (
            await processors.scheduling_history.search_session_history.wait_for_complete(
                SearchSessionHistoryAction(querier=querier)
            )
        )

        resp = ListSessionHistoryResponse(
            items=[
                self._adapter.convert_session_history_to_dto(h) for h in action_result.histories
            ],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def search_deployment_history(
        self,
        body: BodyParam[SearchDeploymentHistoryRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Search deployment history."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can search scheduling history.")

        querier = self._adapter.build_deployment_history_querier(body.parsed)

        action_result = (
            await processors.scheduling_history.search_deployment_history.wait_for_complete(
                SearchDeploymentHistoryAction(querier=querier)
            )
        )

        resp = ListDeploymentHistoryResponse(
            items=[
                self._adapter.convert_deployment_history_to_dto(h) for h in action_result.histories
            ],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def search_route_history(
        self,
        body: BodyParam[SearchRouteHistoryRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Search route history."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can search scheduling history.")

        querier = self._adapter.build_route_history_querier(body.parsed)

        action_result = await processors.scheduling_history.search_route_history.wait_for_complete(
            SearchRouteHistoryAction(querier=querier)
        )

        resp = ListRouteHistoryResponse(
            items=[self._adapter.convert_route_history_to_dto(h) for h in action_result.histories],
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
    """Create aiohttp application for scheduling history API endpoints."""
    app = web.Application()
    app["api_versions"] = (4, 5)
    app["prefix"] = "scheduling-history"

    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    api_handler = SchedulingHistoryAPIHandler()

    # Session history routes
    cors.add(app.router.add_route("POST", "/sessions/search", api_handler.search_session_history))

    # Deployment history routes
    cors.add(
        app.router.add_route("POST", "/deployments/search", api_handler.search_deployment_history)
    )

    # Route history routes
    cors.add(app.router.add_route("POST", "/routes/search", api_handler.search_route_history))

    return app, []
