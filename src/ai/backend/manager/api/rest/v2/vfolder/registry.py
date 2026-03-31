"""Route registry for v2 VFolder endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps

    from .handler import V2VFolderHandler


def register_v2_vfolder_routes(
    handler: V2VFolderHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Build and return the route registry for VFolder endpoints."""
    registry = RouteRegistry.create("vfolders", route_deps.cors_options)

    registry.add(
        "POST",
        "/projects/{project_id}/search",
        handler.project_search,
        middlewares=[auth_required],
    )

    return registry
