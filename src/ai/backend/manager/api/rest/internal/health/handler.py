"""Internal health check handler using constructor dependency injection."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

from aiohttp import web

from ai.backend.common.dto.internal.health import (
    ConnectivityCheckResponse,
    HealthResponse,
    HealthStatus,
)
from ai.backend.manager import __version__
from ai.backend.manager.dto.context import RequestCtx

if TYPE_CHECKING:
    from ai.backend.common.health_checker.probe import HealthProbe


_COMPONENT_NAME = "manager"


def _build_detail_response(connectivity: ConnectivityCheckResponse) -> web.Response:
    """Detail /health — always 200; informational tier failures reported as
    DEGRADED in the body but not surfaced via HTTP status."""
    response = HealthResponse(
        status=HealthStatus.OK if connectivity.overall_healthy else HealthStatus.DEGRADED,
        version=__version__,
        component=_COMPONENT_NAME,
        connectivity=connectivity,
    )
    return web.json_response(response.model_dump(mode="json"))


def _build_probe_response(connectivity: ConnectivityCheckResponse) -> web.Response:
    """/livez, /readyz — 503 when any gating check fails so K8s probes trip."""
    is_healthy = connectivity.overall_healthy
    response = HealthResponse(
        status=HealthStatus.OK if is_healthy else HealthStatus.ERROR,
        version=__version__,
        component=_COMPONENT_NAME,
        connectivity=connectivity,
    )
    return web.json_response(
        response.model_dump(mode="json"),
        status=HTTPStatus.OK if is_healthy else HTTPStatus.SERVICE_UNAVAILABLE,
    )


class InternalHealthHandler:
    _health_probe: HealthProbe

    def __init__(self, *, health_probe: HealthProbe) -> None:
        self._health_probe = health_probe

    async def hello(self, request_ctx: RequestCtx) -> web.Response:
        """Aggregated health (union of liveness and readiness)."""
        request_ctx.request["do_not_print_access_log"] = True
        connectivity = await self._health_probe.get_connectivity_status()
        return _build_detail_response(connectivity)

    async def livez(self, request_ctx: RequestCtx) -> web.Response:
        """Liveness probe — reports only liveness-registered checkers."""
        request_ctx.request["do_not_print_access_log"] = True
        connectivity = await self._health_probe.get_liveness_status()
        return _build_probe_response(connectivity)

    async def readyz(self, request_ctx: RequestCtx) -> web.Response:
        """Readiness probe — reports only readiness-registered checkers."""
        request_ctx.request["do_not_print_access_log"] = True
        connectivity = await self._health_probe.get_readiness_status()
        return _build_probe_response(connectivity)
