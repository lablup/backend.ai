"""Backward-compatible create_app() shim for the RBAC module.

The handler logic has been migrated to
``ai.backend.manager.api.rest.rbac.handler.RBACHandler`` using constructor
dependency injection.  This module provides ``create_app()`` so that the
legacy subapp loading in server.py continues to work.

Once server.py is updated to call ``register_routes()`` directly, this
module can be removed.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

import aiohttp_cors
from aiohttp import web

from ai.backend.manager.api.context import RootContext
from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.rbac.handler import RBACHandler
from ai.backend.manager.api.rest.routing import _wrap_api_handler
from ai.backend.manager.api.types import CORSOptions, WebMiddleware

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import WebRequestHandler

__all__ = ("create_app",)


def _make_route_handler(method_name: str) -> WebRequestHandler:
    """Create a lazy-initialized route handler that delegates to ``RBACHandler``.

    The handler is created on the first request because ``Processors``
    is not yet available at ``create_app()`` time.
    """
    _handler: list[RBACHandler | None] = [None]
    _wrapped: list[WebRequestHandler | None] = [None]

    async def dispatch(request: web.Request) -> web.StreamResponse:
        if _handler[0] is None:
            root_ctx: RootContext = request.app["_root.context"]
            _handler[0] = RBACHandler(processors=root_ctx.processors)
        if (wrapped := _wrapped[0]) is None:
            _wrapped[0] = wrapped = _wrap_api_handler(getattr(_handler[0], method_name))
        return await wrapped(request)

    return auth_required(dispatch)


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    """Create aiohttp application for RBAC API endpoints.

    This is a backward-compatible shim.  The canonical handler lives in
    ``ai.backend.manager.api.rest.rbac.handler.RBACHandler`` and the
    forward-looking entry point is
    ``ai.backend.manager.api.rest.rbac.register_routes()``.
    """
    app = web.Application()
    app["api_versions"] = (4, 5)
    app["prefix"] = "admin/rbac"
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)

    # Role management routes
    cors.add(app.router.add_route("POST", "/roles", _make_route_handler("create_role")))
    cors.add(app.router.add_route("POST", "/roles/search", _make_route_handler("search_roles")))
    cors.add(app.router.add_route("GET", "/roles/{role_id}", _make_route_handler("get_role")))
    cors.add(app.router.add_route("PATCH", "/roles/{role_id}", _make_route_handler("update_role")))
    cors.add(app.router.add_route("POST", "/roles/delete", _make_route_handler("delete_role")))
    cors.add(app.router.add_route("POST", "/roles/purge", _make_route_handler("purge_role")))

    # Role assignment routes
    cors.add(app.router.add_route("POST", "/roles/assign", _make_route_handler("assign_role")))
    cors.add(app.router.add_route("POST", "/roles/revoke", _make_route_handler("revoke_role")))
    cors.add(
        app.router.add_route(
            "POST",
            "/roles/{role_id}/assigned-users/search",
            _make_route_handler("search_assigned_users"),
        )
    )

    # Scope routes
    cors.add(app.router.add_route("GET", "/scope-types", _make_route_handler("get_scope_types")))
    cors.add(
        app.router.add_route(
            "POST",
            "/scopes/{scope_type}/search",
            _make_route_handler("search_scopes"),
        )
    )

    # Entity routes
    cors.add(app.router.add_route("GET", "/entity-types", _make_route_handler("get_entity_types")))
    cors.add(
        app.router.add_route(
            "POST",
            "/scopes/{scope_type}/{scope_id}/entities/{entity_type}/search",
            _make_route_handler("search_entities"),
        )
    )

    return app, []
