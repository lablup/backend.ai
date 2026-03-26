"""Route registry for REST v2 resource usage endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2ResourceUsageHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_resource_usage_routes(
    handler: V2ResourceUsageHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 resource usage routes and return the sub-registry."""
    registry = RouteRegistry.create("resource-usage", route_deps.cors_options)

    registry.add(
        "POST",
        "/domains/search",
        handler.admin_search_domain,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/projects/search",
        handler.admin_search_project,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/users/search",
        handler.admin_search_user,
        middlewares=[superadmin_required],
    )

    return registry
