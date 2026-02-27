"""Backward-compatible create_app() shim for the session template module.

All session template handler logic has been migrated to:

* ``api.rest.session_template.handler`` — SessionTemplateHandler class
* ``api.rest.session_template`` — register_routes()

This module keeps the ``create_app()`` entry-point so that
``server.py`` continues to mount the sub-application without modification.
"""

from __future__ import annotations

from collections.abc import Iterable

from aiohttp import web

from ai.backend.manager.api.manager import READ_ALLOWED, server_status_required
from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.session_template.handler import SessionTemplateHandler

from .types import CORSOptions, WebMiddleware


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["api_versions"] = (4, 5)
    app["prefix"] = "template/session"

    handler = SessionTemplateHandler()
    registry = RouteRegistry(app, default_cors_options)
    _middlewares = [server_status_required(READ_ALLOWED), auth_required]

    registry.add("POST", "", handler.create, middlewares=_middlewares)
    registry.add("GET", "", handler.list_templates, middlewares=_middlewares)
    registry.add("GET", "/{template_id}", handler.get, middlewares=_middlewares)
    registry.add("PUT", "/{template_id}", handler.update, middlewares=_middlewares)
    registry.add("DELETE", "/{template_id}", handler.delete, middlewares=_middlewares)

    return app, []
