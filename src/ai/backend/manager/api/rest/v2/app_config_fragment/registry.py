"""Route registry for REST v2 app config fragment endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2AppConfigFragmentHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_app_config_fragment_routes(
    handler: V2AppConfigFragmentHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register REST v2 app config fragment routes (admin-only).

    App config fragments are managed by superadmins only; there are no user-facing endpoints.

    Layout:
        POST   /admin/search      system-wide paginated search   (superadmin)
    """
    registry = RouteRegistry.create("app-config-fragments", route_deps.cors_options)
    registry.add("POST", "/admin/search", handler.admin_search, middlewares=[superadmin_required])
    return registry
