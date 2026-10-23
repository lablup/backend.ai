"""Route registry for REST v2 system session environ endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2SystemSessionEnvironHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_system_session_environ_routes(
    handler: V2SystemSessionEnvironHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 system session environ routes and return the sub-registry."""
    registry = RouteRegistry.create("system-session-environs", route_deps.cors_options)

    registry.add(
        "POST",
        "/search",
        handler.admin_search,
        middlewares=[superadmin_required],
    )

    return registry
