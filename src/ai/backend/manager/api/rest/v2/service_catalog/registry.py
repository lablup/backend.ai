"""Route registry for REST v2 service catalog endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2ServiceCatalogHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_service_catalog_routes(
    handler: V2ServiceCatalogHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 service catalog routes and return the sub-registry."""
    registry = RouteRegistry.create("service-catalogs", route_deps.cors_options)

    registry.add(
        "POST",
        "/search",
        handler.admin_search_service_catalogs,
        middlewares=[superadmin_required],
    )

    return registry
