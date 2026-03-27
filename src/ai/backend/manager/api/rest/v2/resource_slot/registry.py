"""Route registry for REST v2 resource slot endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2ResourceSlotHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_resource_slot_routes(
    handler: V2ResourceSlotHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 resource slot routes and return the sub-registry."""
    registry = RouteRegistry.create("resource-slots", route_deps.cors_options)

    registry.add(
        "POST",
        "/slot-types/search",
        handler.search_slot_types,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/agent-resources/search",
        handler.search_agent_resources,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/allocations/search",
        handler.search_allocations,
        middlewares=[superadmin_required],
    )

    return registry
