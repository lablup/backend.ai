"""Route registry for REST v2 login history endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2LoginHistoryHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_login_history_routes(
    handler: V2LoginHistoryHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 login history routes and return the sub-registry."""
    registry = RouteRegistry.create("login-history", route_deps.cors_options)

    registry.add(
        "POST",
        "/search",
        handler.admin_search,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/my/search",
        handler.my_search,
        middlewares=[auth_required],
    )

    return registry
