"""Public health check handler — simple liveness probe."""

from __future__ import annotations

from aiohttp import web

from ai.backend.manager import __version__
from ai.backend.manager.dto.context import RequestCtx


class HealthHandler:
    async def hello(self, request_ctx: RequestCtx) -> web.Response:
        """Simple liveness probe — returns 200 OK with version."""
        request_ctx.request["do_not_print_access_log"] = True
        return web.json_response({"status": "ok", "version": __version__})
