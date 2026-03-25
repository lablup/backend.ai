"""Route registry for REST v2 resource group endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2ResourceGroupHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_resource_group_routes(
    handler: V2ResourceGroupHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 resource group routes and return the sub-registry."""
    registry = RouteRegistry.create("resource-groups", route_deps.cors_options)

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
        "/{name}",
        handler.get,
        middlewares=[superadmin_required],
    )
    registry.add(
        "PATCH",
        "/{name}",
        handler.update,
        middlewares=[superadmin_required],
    )
    registry.add(
        "DELETE",
        "/{name}",
        handler.delete,
        middlewares=[superadmin_required],
    )
    registry.add(
        "GET",
        "/{name}/resource-info",
        handler.get_resource_info,
        middlewares=[superadmin_required],
    )
    registry.add(
        "PATCH",
        "/{name}/fair-share-spec",
        handler.update_fair_share_spec,
        middlewares=[superadmin_required],
    )
    registry.add(
        "PATCH",
        "/{name}/config",
        handler.update_config,
        middlewares=[superadmin_required],
    )

    return registry
