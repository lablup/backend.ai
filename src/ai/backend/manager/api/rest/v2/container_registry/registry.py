"""Route registry for REST v2 container registry endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2ContainerRegistryHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_container_registry_routes(
    handler: V2ContainerRegistryHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 container registry routes and return the sub-registry."""
    registry = RouteRegistry.create("container-registries", route_deps.cors_options)

    registry.add(
        "POST",
        "/search",
        handler.admin_search_container_registries,
        middlewares=[superadmin_required],
    )

    return registry
