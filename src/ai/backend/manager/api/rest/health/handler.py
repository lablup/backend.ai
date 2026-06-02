"""Public health check handler — status-only liveness / readiness probes."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

from aiohttp import web

from ai.backend.manager import __version__
from ai.backend.manager.dto.context import RequestCtx

if TYPE_CHECKING:
    from ai.backend.common.health_checker.probe import HealthProbe


class HealthHandler:
    """Public-facing health endpoints.

    ``/health`` returns a minimal liveness payload (version only — never the
    internal connectivity matrix, which would leak deployment topology).
    ``/livez`` and ``/readyz`` are status-only K8s-style probes that mirror
    the internal liveness / readiness checks but omit the response body.
    """

    _health_probe: HealthProbe

    def __init__(self, *, health_probe: HealthProbe) -> None:
        self._health_probe = health_probe

    async def hello(self, request_ctx: RequestCtx) -> web.Response:
        """Simple liveness probe — returns 200 OK with version."""
        request_ctx.request["do_not_print_access_log"] = True
        return web.json_response({"status": "ok", "version": __version__})

    async def livez(self, request_ctx: RequestCtx) -> web.Response:
        """Liveness probe — 200 / 503 based on liveness-tier health, empty body."""
        request_ctx.request["do_not_print_access_log"] = True
        connectivity = await self._health_probe.get_liveness_status()
        return web.Response(
            status=HTTPStatus.OK if connectivity.overall_healthy else HTTPStatus.SERVICE_UNAVAILABLE
        )

    async def readyz(self, request_ctx: RequestCtx) -> web.Response:
        """Readiness probe — 200 / 503 based on readiness-tier health, empty body."""
        request_ctx.request["do_not_print_access_log"] = True
        connectivity = await self._health_probe.get_readiness_status()
        return web.Response(
            status=HTTPStatus.OK if connectivity.overall_healthy else HTTPStatus.SERVICE_UNAVAILABLE
        )
