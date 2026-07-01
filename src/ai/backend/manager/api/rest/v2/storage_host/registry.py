"""Route registry for v2 storage host endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps

    from .handler import V2StorageHostHandler


def register_v2_storage_host_routes(
    handler: V2StorageHostHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Build and return the route registry for storage host endpoints."""
    registry = RouteRegistry.create("storage-hosts", route_deps.cors_options)

    registry.add(
        "GET",
        "/my/permissions",
        handler.my_storage_host_permissions,
        middlewares=[auth_required],
    )

    return registry
