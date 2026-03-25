"""Route registry for REST v2 scheduling history endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2SchedulingHistoryHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_scheduling_history_routes(
    handler: V2SchedulingHistoryHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 scheduling history routes and return the sub-registry."""
    registry = RouteRegistry.create("scheduling-history", route_deps.cors_options)

    # Session history
    registry.add(
        "POST",
        "/sessions/search",
        handler.admin_search_session_history,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/sessions/{session_id}/search",
        handler.admin_session_scoped_search,
        middlewares=[superadmin_required],
    )

    # Deployment history
    registry.add(
        "POST",
        "/deployments/search",
        handler.admin_search_deployment_history,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/deployments/{deployment_id}/search",
        handler.admin_deployment_scoped_search,
        middlewares=[superadmin_required],
    )

    # Route history
    registry.add(
        "POST",
        "/routes/search",
        handler.admin_search_route_history,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/routes/{route_id}/search",
        handler.admin_route_scoped_search,
        middlewares=[superadmin_required],
    )

    return registry
