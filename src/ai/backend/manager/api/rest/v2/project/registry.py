"""Route registration for v2 project endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2ProjectHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_project_routes(
    handler: V2ProjectHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all v2 project routes."""
    reg = RouteRegistry.create("projects", route_deps.cors_options)
    reg.add("GET", "/{project_id}", handler.get, middlewares=[auth_required])
    reg.add("POST", "/search", handler.admin_search, middlewares=[superadmin_required])
    return reg
