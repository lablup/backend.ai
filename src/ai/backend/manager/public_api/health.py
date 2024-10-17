from __future__ import annotations

import logging

from aiohttp import web

from ai.backend.common.logging import BraceStyleAdapter

from .types import CORSOptions

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


async def init(app: web.Application) -> None:
    pass


async def shutdown(app: web.Application) -> None:
    pass


def create_app(default_cors_options: CORSOptions):
    app = web.Application()
    app["prefix"] = "health"
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    return app, []
