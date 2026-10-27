"""Route registry for REST v2 vfolder auto-mount endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2VFolderAutoMountHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_vfolder_auto_mount_routes(
    handler: V2VFolderAutoMountHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 vfolder auto-mount routes and return the sub-registry."""
    registry = RouteRegistry.create("vfolder-auto-mounts", route_deps.cors_options)

    registry.add("POST", "", handler.create, middlewares=[auth_required])
    registry.add("POST", "/scoped/search", handler.scoped_search, middlewares=[auth_required])
    registry.add("PATCH", "/{vfolder_auto_mount_id}", handler.update, middlewares=[auth_required])
    registry.add(
        "POST", "/{vfolder_auto_mount_id}/delete", handler.delete, middlewares=[auth_required]
    )

    return registry
