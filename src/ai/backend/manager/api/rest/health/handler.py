"""Public health check handler using constructor dependency injection."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from ai.backend.common.dto.internal.health import HealthResponse, HealthStatus
from ai.backend.manager import __version__

if TYPE_CHECKING:
    from ai.backend.common.health_checker.probe import HealthProbe


class HealthHandler:
    _health_probe: HealthProbe

    def __init__(self, *, health_probe: HealthProbe) -> None:
        self._health_probe = health_probe

    async def hello(self, request: web.Request) -> web.Response:
        """Health check endpoint with dependency connectivity status."""
        request["do_not_print_access_log"] = True
        connectivity = await self._health_probe.get_connectivity_status()
        response = HealthResponse(
            status=HealthStatus.OK if connectivity.overall_healthy else HealthStatus.DEGRADED,
            version=__version__,
            component="manager",
            connectivity=connectivity,
        )
        return web.json_response(response.model_dump(mode="json"))
