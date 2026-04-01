"""Route registry for REST v2 resource preset endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2ResourcePresetHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_resource_preset_routes(
    handler: V2ResourcePresetHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 resource preset routes and return the sub-registry."""
    registry = RouteRegistry.create("resource-presets", route_deps.cors_options)

    registry.add(
        "POST",
        "/search",
        handler.search,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "",
        handler.create,
        middlewares=[superadmin_required],
    )
    registry.add(
        "GET",
        "/{preset_id}",
        handler.get,
        middlewares=[superadmin_required],
    )
    registry.add(
        "PATCH",
        "/{preset_id}",
        handler.update,
        middlewares=[superadmin_required],
    )
    registry.add(
        "DELETE",
        "/{preset_id}",
        handler.delete,
        middlewares=[superadmin_required],
    )

    return registry
