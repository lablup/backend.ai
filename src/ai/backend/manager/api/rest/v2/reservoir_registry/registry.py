"""Route registry for REST v2 Reservoir registry endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2ReservoirRegistryHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_reservoir_registry_routes(
    handler: V2ReservoirRegistryHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 Reservoir registry routes and return the sub-registry."""
    registry = RouteRegistry.create("reservoir-registries", route_deps.cors_options)

    registry.add(
        "POST",
        "",
        handler.create,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/search",
        handler.search,
        middlewares=[superadmin_required],
    )
    registry.add(
        "GET",
        "/{registry_id}",
        handler.get,
        middlewares=[superadmin_required],
    )
    registry.add(
        "PATCH",
        "/{registry_id}",
        handler.update,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/delete",
        handler.delete,
        middlewares=[superadmin_required],
    )

    return registry
