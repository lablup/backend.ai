"""Client SDK functions for scheduling history."""

from __future__ import annotations

from ai.backend.client.request import Request
from ai.backend.common.dto.manager.scheduling_history import (
    ListDeploymentHistoryResponse,
    ListRouteHistoryResponse,
    ListSessionHistoryResponse,
    SearchDeploymentHistoryRequest,
    SearchRouteHistoryRequest,
    SearchSessionHistoryRequest,
)

from .base import BaseFunction, api_function

__all__ = ("SchedulingHistory",)


class SchedulingHistory(BaseFunction):
    """
    Provides functions to interact with scheduling history.
    Supports session, deployment, and route scheduling history.
    Requires superadmin privileges.
    """

    @api_function
    @classmethod
    async def list_session_history(
        cls,
        request: SearchSessionHistoryRequest,
    ) -> ListSessionHistoryResponse:
        """
        Search session scheduling history.

        :param request: Session history search request
        :returns: List of session scheduling history records
        """
        rqst = Request("POST", "/scheduling-history/sessions/search")
        rqst.set_json(request.model_dump(mode="json", exclude_none=True))
        async with rqst.fetch() as resp:
            data = await resp.json()
            return ListSessionHistoryResponse.model_validate(data)

    @api_function
    @classmethod
    async def list_deployment_history(
        cls,
        request: SearchDeploymentHistoryRequest,
    ) -> ListDeploymentHistoryResponse:
        """
        Search deployment scheduling history.

        :param request: Deployment history search request
        :returns: List of deployment history records
        """
        rqst = Request("POST", "/scheduling-history/deployments/search")
        rqst.set_json(request.model_dump(mode="json", exclude_none=True))
        async with rqst.fetch() as resp:
            data = await resp.json()
            return ListDeploymentHistoryResponse.model_validate(data)

    @api_function
    @classmethod
    async def list_route_history(
        cls,
        request: SearchRouteHistoryRequest,
    ) -> ListRouteHistoryResponse:
        """
        Search route scheduling history.

        :param request: Route history search request
        :returns: List of route history records
        """
        rqst = Request("POST", "/scheduling-history/routes/search")
        rqst.set_json(request.model_dump(mode="json", exclude_none=True))
        async with rqst.fetch() as resp:
            data = await resp.json()
            return ListRouteHistoryResponse.model_validate(data)
