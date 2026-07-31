"""Route registry for REST v2 idle checker endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.v2.idle_checker.handler import V2IdleCheckerHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_idle_checker_routes(
    handler: V2IdleCheckerHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 idle checker routes (superadmin only)."""
    registry = RouteRegistry.create("idle-checkers", route_deps.cors_options)

    registry.add("POST", "/", handler.admin_create, middlewares=[superadmin_required])
    registry.add("POST", "/search", handler.admin_search, middlewares=[superadmin_required])
    registry.add(
        "PATCH",
        "/{idle_checker_id}",
        handler.admin_update,
        middlewares=[superadmin_required],
    )
    registry.add(
        "DELETE",
        "/{idle_checker_id}",
        handler.admin_purge,
        middlewares=[superadmin_required],
    )

    return registry
