"""Scheduling history handler class using constructor dependency injection."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Final

from ai.backend.common.api_handlers import APIResponse, BodyParam
from ai.backend.common.dto.manager.scheduling_history import (
    ListDeploymentHistoryResponse,
    ListRouteHistoryResponse,
    ListSessionHistoryResponse,
    PaginationInfo,
    SearchDeploymentHistoryRequest,
    SearchRouteHistoryRequest,
    SearchSessionHistoryRequest,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.dto.context import UserContext
from ai.backend.manager.services.processors import Processors
from ai.backend.manager.services.scheduling_history.actions import (
    SearchDeploymentHistoryAction,
    SearchRouteHistoryAction,
    SearchSessionHistoryAction,
)

from .adapter import SchedulingHistoryAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class SchedulingHistoryHandler:
    """Scheduling history API handler with constructor-injected dependencies."""

    def __init__(self, *, processors: Processors) -> None:
        self._processors = processors
        self._adapter = SchedulingHistoryAdapter()

    async def search_session_history(
        self,
        body: BodyParam[SearchSessionHistoryRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Search session scheduling history."""
        log.info("SEARCH_SESSION_HISTORY (ak:{})", ctx.access_key)

        querier = self._adapter.build_session_history_querier(body.parsed)

        action_result = (
            await self._processors.scheduling_history.search_session_history.wait_for_complete(
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

    async def search_deployment_history(
        self,
        body: BodyParam[SearchDeploymentHistoryRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Search deployment history."""
        log.info("SEARCH_DEPLOYMENT_HISTORY (ak:{})", ctx.access_key)

        querier = self._adapter.build_deployment_history_querier(body.parsed)

        action_result = (
            await self._processors.scheduling_history.search_deployment_history.wait_for_complete(
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

    async def search_route_history(
        self,
        body: BodyParam[SearchRouteHistoryRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Search route history."""
        log.info("SEARCH_ROUTE_HISTORY (ak:{})", ctx.access_key)

        querier = self._adapter.build_route_history_querier(body.parsed)

        action_result = (
            await self._processors.scheduling_history.search_route_history.wait_for_complete(
                SearchRouteHistoryAction(querier=querier)
            )
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
