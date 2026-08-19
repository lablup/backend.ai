"""Route registry for REST v2 idle checker assignment endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2IdleCheckerAssignmentHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_idle_checker_assignment_routes(
    handler: V2IdleCheckerAssignmentHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 idle checker assignment routes and return the sub-registry."""
    registry = RouteRegistry.create("idle-checker-assignments", route_deps.cors_options)

    registry.add("POST", "/", handler.admin_create, middlewares=[superadmin_required])
    registry.add("POST", "/search", handler.admin_search, middlewares=[superadmin_required])
    registry.add("POST", "/scoped/search", handler.scoped_search, middlewares=[auth_required])
    registry.add(
        "PATCH",
        "/{idle_checker_assignment_id}",
        handler.update,
        middlewares=[auth_required],
    )
    registry.add(
        "DELETE",
        "/{idle_checker_assignment_id}",
        handler.purge,
        middlewares=[auth_required],
    )

    return registry
