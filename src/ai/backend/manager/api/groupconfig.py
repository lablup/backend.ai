"""Backward-compatibility shim for the group config module.

All group config (dotfile) logic has been migrated to:

* ``api.rest.groupconfig`` — GroupConfigHandler + route registration

This module keeps ``create_app()`` so that the existing server bootstrap
(``server.py``) continues to work without modification.
"""

from __future__ import annotations

from collections.abc import Iterable

from aiohttp import web

from ai.backend.manager.api.rest.groupconfig.handler import GroupConfigHandler
from ai.backend.manager.api.rest.middleware.auth import admin_required, auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .manager import READ_ALLOWED, server_status_required
from .types import CORSOptions, WebMiddleware

_status_readable = server_status_required(READ_ALLOWED)


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["api_versions"] = (4, 5)
    app["prefix"] = "group-config"
    handler = GroupConfigHandler()
    registry = RouteRegistry(app, default_cors_options)
    registry.add(
        "POST", "/dotfiles", handler.create, middlewares=[_status_readable, admin_required]
    )
    registry.add(
        "GET", "/dotfiles", handler.list_or_get, middlewares=[_status_readable, auth_required]
    )
    registry.add(
        "PATCH", "/dotfiles", handler.update, middlewares=[_status_readable, admin_required]
    )
    registry.add(
        "DELETE", "/dotfiles", handler.delete, middlewares=[_status_readable, admin_required]
    )
    return app, []
