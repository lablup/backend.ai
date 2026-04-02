"""Route registry for REST v2 login session endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2LoginSessionHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_login_session_routes(
    handler: V2LoginSessionHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 login session routes and return the sub-registry."""
    registry = RouteRegistry.create("login-sessions", route_deps.cors_options)

    registry.add(
        "POST",
        "/search",
        handler.admin_search,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/revoke",
        handler.admin_revoke,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/my/search",
        handler.my_search,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/my/revoke",
        handler.my_revoke,
        middlewares=[auth_required],
    )

    return registry
