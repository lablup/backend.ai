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
from ai.backend.manager.models.scheduling_history.searchers import (
    DeploymentHistorySearcher,
    RouteHistorySearcher,
    SessionSchedulingHistorySearcher,
)
from ai.backend.manager.models.specs.searcher import GlobalSearcher
from ai.backend.manager.services.scheduling_history.actions import (
    SearchDeploymentHistoryAction,
    SearchRouteHistoryAction,
    SearchSessionHistoryAction,
)
from ai.backend.manager.services.scheduling_history.processors import SchedulingHistoryProcessors

from .adapter import SchedulingHistoryAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class SchedulingHistoryHandler:
    """Scheduling history API handler with constructor-injected dependencies."""

    def __init__(self, *, scheduling_history: SchedulingHistoryProcessors) -> None:
        self._scheduling_history = scheduling_history
        self._adapter = SchedulingHistoryAdapter()

    async def search_session_history(
        self,
        body: BodyParam[SearchSessionHistoryRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Search session scheduling history."""

        querier = self._adapter.build_session_history_querier(body.parsed)

        action_result = await self._scheduling_history.search_session_history.run(
            SearchSessionHistoryAction(
                searcher=GlobalSearcher(
                    used_by=(),
                    searcher=SessionSchedulingHistorySearcher(
                        pagination=querier.pagination,
                        conditions=querier.conditions,
                        orders=querier.orders,
                    ),
                )
            )
        )

        resp = ListSessionHistoryResponse(
            items=[self._adapter.convert_session_history_to_dto(h) for h in action_result.items],
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

        querier = self._adapter.build_deployment_history_querier(body.parsed)

        action_result = await self._scheduling_history.search_deployment_history.run(
            SearchDeploymentHistoryAction(
                searcher=GlobalSearcher(
                    used_by=(),
                    searcher=DeploymentHistorySearcher(
                        pagination=querier.pagination,
                        conditions=querier.conditions,
                        orders=querier.orders,
                    ),
                )
            )
        )

        resp = ListDeploymentHistoryResponse(
            items=[self._adapter.convert_deployment_history_to_dto(h) for h in action_result.items],
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

        querier = self._adapter.build_route_history_querier(body.parsed)

        action_result = await self._scheduling_history.search_route_history.run(
            SearchRouteHistoryAction(
                searcher=GlobalSearcher(
                    used_by=(),
                    searcher=RouteHistorySearcher(
                        pagination=querier.pagination,
                        conditions=querier.conditions,
                        orders=querier.orders,
                    ),
                )
            )
        )

        resp = ListRouteHistoryResponse(
            items=[self._adapter.convert_route_history_to_dto(h) for h in action_result.items],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)
