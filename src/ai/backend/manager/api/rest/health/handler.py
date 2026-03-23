"""Public health check handler — simple liveness probe."""

from __future__ import annotations

from aiohttp import web

from ai.backend.manager import __version__


class HealthHandler:
    async def hello(self, request: web.Request) -> web.Response:
        """Simple liveness probe — returns 200 OK with version."""
        request["do_not_print_access_log"] = True
        return web.json_response({"status": "ok", "version": __version__})
