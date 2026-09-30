"""Public health check handler — liveness / readiness probes."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

from aiohttp import web

from ai.backend.manager import __version__
from ai.backend.manager.api.rest.shutdown import ServerDrainNotifier
from ai.backend.manager.dto.context import RequestCtx
from ai.backend.manager.errors.common import ManagerDraining

if TYPE_CHECKING:
    from ai.backend.common.health_checker.probe import HealthProbe


class HealthHandler:
    """Public-facing health endpoints.

    ``/health`` returns a minimal liveness payload (version only — never the
    internal connectivity matrix, which would leak deployment topology).
    ``/livez`` and ``/readyz`` are status-only K8s-style probes that mirror
    the internal liveness / readiness checks but omit the response body except for draining errors.
    """

    _health_probe: HealthProbe
    _drain_notifier: ServerDrainNotifier

    def __init__(self, *, health_probe: HealthProbe, drain_notifier: ServerDrainNotifier) -> None:
        self._health_probe = health_probe
        self._drain_notifier = drain_notifier

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
        """Readiness probe; draining returns a 503 problem response."""
        request_ctx.request["do_not_print_access_log"] = True
        if self._drain_notifier.is_draining:
            raise ManagerDraining()
        connectivity = await self._health_probe.get_readiness_status()
        return web.Response(
            status=HTTPStatus.OK if connectivity.overall_healthy else HTTPStatus.SERVICE_UNAVAILABLE
        )
