"""Route registry for v2 object storage endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps

    from .handler import V2ObjectStorageHandler


def register_v2_object_storage_routes(
    handler: V2ObjectStorageHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Build and return the route registry for object storage endpoints."""
    registry = RouteRegistry.create("object-storages", route_deps.cors_options)

    registry.add("POST", "", handler.create, middlewares=[superadmin_required])
    registry.add("GET", "/{storage_id}", handler.get, middlewares=[superadmin_required])
    registry.add("PATCH", "/{storage_id}", handler.update, middlewares=[superadmin_required])
    registry.add("POST", "/search", handler.search, middlewares=[superadmin_required])
    registry.add("POST", "/delete", handler.delete, middlewares=[superadmin_required])

    return registry
