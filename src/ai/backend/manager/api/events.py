"""Backward-compatibility shim for the events module.

All event streaming handler logic has been migrated to:

* ``api.rest.events.handler`` — EventsHandler class + lifecycle helpers
* ``api.rest.events`` — register_routes()

This module keeps ``create_app()`` so that the existing server bootstrap
(``server.py``) continues to work without modification.
"""

from __future__ import annotations

from collections.abc import Iterable

from aiohttp import web

from ai.backend.manager.api.rest.events import register_routes
from ai.backend.manager.api.rest.events.handler import (
    PrivateContext,
    events_app_ctx,
    events_shutdown,
)
from ai.backend.manager.api.rest.routing import RouteRegistry

from .types import CORSOptions, WebMiddleware


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["prefix"] = "events"
    app["events.context"] = PrivateContext()
    app["api_versions"] = (3, 4)
    app.on_shutdown.append(events_shutdown)
    app.cleanup_ctx.append(events_app_ctx)
    registry = RouteRegistry(app, default_cors_options)
    register_routes(registry)
    return app, []
