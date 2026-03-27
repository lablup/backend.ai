"""Route registry for REST v2 image endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2ImageHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_image_routes(
    handler: V2ImageHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 image routes and return the sub-registry."""
    registry = RouteRegistry.create("images", route_deps.cors_options)

    registry.add(
        "POST",
        "/search",
        handler.admin_search_images,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/aliases/search",
        handler.admin_search_image_aliases,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/forget",
        handler.admin_forget,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/purge",
        handler.admin_purge,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/alias",
        handler.admin_alias,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/dealias",
        handler.admin_dealias,
        middlewares=[superadmin_required],
    )
    registry.add(
        "PATCH",
        "",
        handler.admin_update,
        middlewares=[superadmin_required],
    )

    return registry
