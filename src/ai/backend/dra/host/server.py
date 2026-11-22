"""The plugin host's side of the bridge API: aiohttp on a Unix socket."""

from __future__ import annotations

import logging
from pathlib import Path

from aiohttp import web

from ai.backend.common.exception import BackendAIError
from ai.backend.dra.bridge import (
    BRIDGE_VERSION,
    PrepareRequest,
    PrepareResponse,
    UnprepareRequest,
)
from ai.backend.dra.host.plugin_host import PluginHost
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))


def build_app(host: PluginHost) -> web.Application:
    async def devices(_request: web.Request) -> web.Response:
        return web.json_response((await host.list_devices()).model_dump(mode="json"))

    async def health(_request: web.Request) -> web.Response:
        return web.json_response({"status": "ok"})

    async def prepare(request: web.Request) -> web.Response:
        body = PrepareRequest.model_validate(await request.json())
        try:
            edits, per_device = await host.prepare(body.claim_uid, body.devices, body.consumed)
        except BackendAIError as e:
            if e.status_code >= 500:
                log.exception("claim prepare failed", claim_uid=body.claim_uid)
            else:
                log.trace("claim prepare refused", claim_uid=body.claim_uid, error=str(e.extra_msg))
            return web.json_response({"error": str(e.extra_msg)}, status=e.status_code)
        response = PrepareResponse(edits=edits, device_cdi_devices=per_device)
        return web.json_response(response.model_dump(mode="json"))

    async def unprepare(request: web.Request) -> web.Response:
        body = UnprepareRequest.model_validate(await request.json())
        try:
            await host.unprepare(body.claim_uid)
        except BackendAIError as e:
            return web.json_response({"error": str(e.extra_msg)}, status=e.status_code)
        return web.json_response({})

    app = web.Application()
    app.router.add_get(f"/{BRIDGE_VERSION}/health", health)
    app.router.add_get(f"/{BRIDGE_VERSION}/devices", devices)
    app.router.add_post(f"/{BRIDGE_VERSION}/prepare", prepare)
    app.router.add_post(f"/{BRIDGE_VERSION}/unprepare", unprepare)
    return app


async def serve(host: PluginHost, socket_path: Path) -> web.AppRunner:
    socket_path.parent.mkdir(parents=True, exist_ok=True)
    socket_path.unlink(missing_ok=True)
    runner = web.AppRunner(build_app(host), access_log=None)
    await runner.setup()
    await web.UnixSite(runner, str(socket_path)).start()
    log.info("plugin host listening", socket_path=str(socket_path))
    return runner
