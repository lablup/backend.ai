"""Route registry for REST v2 scheduling-handler endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2SchedulingHandlerHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_scheduling_handler_routes(
    handler: V2SchedulingHandlerHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 scheduling-handler routes and return the sub-registry."""
    registry = RouteRegistry.create("scheduling-handlers", route_deps.cors_options)

    registry.add(
        "GET",
        "",
        handler.admin_list,
        middlewares=[superadmin_required],
    )

    return registry
