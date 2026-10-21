"""Route registry for REST v2 session group endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2SessionGroupHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_session_group_routes(
    handler: V2SessionGroupHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 session group routes and return the sub-registry."""
    registry = RouteRegistry.create("session-groups", route_deps.cors_options)

    registry.add("GET", "/{session_group_id}", handler.get, middlewares=[auth_required])
    registry.add("POST", "/search", handler.admin_search, middlewares=[superadmin_required])
    registry.add("POST", "/scoped/search", handler.scoped_search, middlewares=[auth_required])
    registry.add("POST", "/{session_group_id}/purge", handler.purge, middlewares=[auth_required])

    return registry
