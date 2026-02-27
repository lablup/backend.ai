"""Backward-compatibility shim for the user config module.

All user config (dotfile) logic has been migrated to:

* ``api.rest.userconfig`` — UserConfigHandler + register_routes()

This module keeps ``create_app()`` so that the existing server bootstrap
(``server.py``) continues to work without modification.
"""

from __future__ import annotations

from collections.abc import Iterable

from aiohttp import web

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.userconfig.handler import UserConfigHandler

from .manager import READ_ALLOWED, server_status_required
from .types import CORSOptions, WebMiddleware

_status_readable = server_status_required(READ_ALLOWED)


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["api_versions"] = (4, 5)
    app["prefix"] = "user-config"
    handler = UserConfigHandler()
    registry = RouteRegistry(app, default_cors_options)
    registry.add("POST", "/dotfiles", handler.create, middlewares=[_status_readable, auth_required])
    registry.add(
        "GET", "/dotfiles", handler.list_or_get, middlewares=[_status_readable, auth_required]
    )
    registry.add(
        "PATCH", "/dotfiles", handler.update, middlewares=[_status_readable, auth_required]
    )
    registry.add(
        "DELETE", "/dotfiles", handler.delete, middlewares=[_status_readable, auth_required]
    )
    registry.add(
        "POST",
        "/bootstrap-script",
        handler.update_bootstrap_script,
        middlewares=[_status_readable, auth_required],
    )
    registry.add(
        "GET",
        "/bootstrap-script",
        handler.get_bootstrap_script,
        middlewares=[_status_readable, auth_required],
    )
    return app, []
