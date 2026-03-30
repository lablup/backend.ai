"""Route registry for v2 storage namespace endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps

    from .handler import V2StorageNamespaceHandler


def register_v2_storage_namespace_routes(
    handler: V2StorageNamespaceHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Build and return the route registry for storage namespace endpoints."""
    registry = RouteRegistry.create("storage-namespaces", route_deps.cors_options)

    registry.add("POST", "", handler.register, middlewares=[superadmin_required])
    registry.add("POST", "/unregister", handler.unregister, middlewares=[superadmin_required])
    registry.add("POST", "/search", handler.search, middlewares=[superadmin_required])
    registry.add(
        "GET",
        "/by-storage/{storage_id}",
        handler.get_by_storage,
        middlewares=[superadmin_required],
    )

    return registry
