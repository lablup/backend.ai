"""Route registry for REST v2 session endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2SessionHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_session_routes(
    handler: V2SessionHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 session routes and return the sub-registry."""
    registry = RouteRegistry.create("sessions", route_deps.cors_options)

    registry.add(
        "POST",
        "/search",
        handler.admin_search_sessions,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/kernels/search",
        handler.admin_search_kernels,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/search-by-agent/{agent_id}",
        handler.admin_search_sessions_by_agent,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/kernels/search-by-agent/{agent_id}",
        handler.admin_search_kernels_by_agent,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/{session_id}/kernels/search",
        handler.admin_search_kernels_by_session,
        middlewares=[superadmin_required],
    )

    return registry
