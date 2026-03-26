"""REST v2 handler for the scheduling history domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.scheduling_history.request import (
    AdminSearchDeploymentHistoriesInput,
    AdminSearchRouteHistoriesInput,
    AdminSearchSessionHistoriesInput,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.v2.path_params import (
    DeploymentIdPathParam,
    RouteIdPathParam,
    SessionIdPathParam,
)

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.scheduling_history import SchedulingHistoryAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2SchedulingHistoryHandler:
    """REST v2 handler for scheduling history operations."""

    def __init__(self, *, adapter: SchedulingHistoryAdapter) -> None:
        self._adapter = adapter

    # ========== Session History ==========

    async def admin_search_session_history(
        self,
        body: BodyParam[AdminSearchSessionHistoriesInput],
    ) -> APIResponse:
        """Search session scheduling histories with admin scope."""
        result = await self._adapter.admin_search_session_history(
            body.parsed,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_session_scoped_search(
        self,
        path: PathParam[SessionIdPathParam],
        body: BodyParam[AdminSearchSessionHistoriesInput],
    ) -> APIResponse:
        """Search session scheduling histories scoped to a specific session."""
        result = await self._adapter.session_scoped_search(
            path.parsed.session_id,
            body.parsed,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    # ========== Deployment History ==========

    async def admin_search_deployment_history(
        self,
        body: BodyParam[AdminSearchDeploymentHistoriesInput],
    ) -> APIResponse:
        """Search deployment histories with admin scope."""
        result = await self._adapter.admin_search_deployment_history(
            body.parsed,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_deployment_scoped_search(
        self,
        path: PathParam[DeploymentIdPathParam],
        body: BodyParam[AdminSearchDeploymentHistoriesInput],
    ) -> APIResponse:
        """Search deployment histories scoped to a specific deployment."""
        result = await self._adapter.deployment_scoped_search(
            path.parsed.deployment_id,
            body.parsed,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    # ========== Route History ==========

    async def admin_search_route_history(
        self,
        body: BodyParam[AdminSearchRouteHistoriesInput],
    ) -> APIResponse:
        """Search route histories with admin scope."""
        result = await self._adapter.admin_search_route_history(
            body.parsed,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_route_scoped_search(
        self,
        path: PathParam[RouteIdPathParam],
        body: BodyParam[AdminSearchRouteHistoriesInput],
    ) -> APIResponse:
        """Search route histories scoped to a specific route."""
        result = await self._adapter.route_scoped_search(
            path.parsed.route_id,
            body.parsed,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
