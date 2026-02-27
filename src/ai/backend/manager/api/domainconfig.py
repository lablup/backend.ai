"""Backward-compatibility shim for the domain config module.

All domain config (dotfile) logic has been migrated to:

* ``api.rest.domainconfig`` — DomainConfigHandler + register_routes()

This module keeps ``create_app()`` so that the existing server bootstrap
(``server.py``) continues to work without modification.
"""

from __future__ import annotations

from collections.abc import Iterable

from aiohttp import web

from ai.backend.manager.api.rest.domainconfig.handler import DomainConfigHandler
from ai.backend.manager.api.rest.middleware.auth import admin_required, auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .types import CORSOptions, WebMiddleware


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["api_versions"] = (4, 5)
    app["prefix"] = "domain-config"
    handler = DomainConfigHandler()
    registry = RouteRegistry(app, default_cors_options)
    registry.add("POST", "/dotfiles", handler.create, middlewares=[admin_required])
    registry.add("GET", "/dotfiles", handler.list_or_get, middlewares=[auth_required])
    registry.add("PATCH", "/dotfiles", handler.update, middlewares=[admin_required])
    registry.add("DELETE", "/dotfiles", handler.delete, middlewares=[admin_required])
    return app, []
