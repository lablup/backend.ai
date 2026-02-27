"""Backward-compatibility shim for the stream module.

All streaming handler logic has been migrated to:

* ``api.rest.stream.handler`` — StreamHandler class + lifecycle helpers
* ``api.rest.stream`` — register_routes()

This module keeps ``create_app()`` so that the existing server bootstrap
(``server.py``) continues to work without modification.
"""

from __future__ import annotations

from collections.abc import Iterable

import aiotools
from aiohttp import web

from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.stream import register_routes
from ai.backend.manager.api.rest.stream.handler import (
    PrivateContext,
    stream_app_ctx,
    stream_shutdown,
)

from .types import CORSOptions, WebMiddleware


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app.cleanup_ctx.append(stream_app_ctx)
    app.on_shutdown.append(stream_shutdown)
    app["prefix"] = "stream"
    app["api_versions"] = (2, 3, 4)
    app["stream.context"] = PrivateContext()
    app["database_ptask_group"] = aiotools.PersistentTaskGroup()
    app["rpc_ptask_group"] = aiotools.PersistentTaskGroup()
    registry = RouteRegistry(app, default_cors_options)
    register_routes(registry)
    return app, []
