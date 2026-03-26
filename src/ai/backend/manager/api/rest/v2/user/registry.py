"""Route registration for v2 user endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2UserHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_user_routes(
    handler: V2UserHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all v2 user routes."""
    reg = RouteRegistry.create("users", route_deps.cors_options)
    reg.add("POST", "/search", handler.admin_search, middlewares=[superadmin_required])
    reg.add("GET", "/{user_id}", handler.get, middlewares=[auth_required])
    reg.add("POST", "", handler.create_user, middlewares=[superadmin_required])
    reg.add("PATCH", "/{user_id}", handler.modify_user, middlewares=[superadmin_required])
    reg.add("POST", "/delete", handler.delete_user, middlewares=[superadmin_required])
    reg.add(
        "POST",
        "/search-by-domain/{domain_name}",
        handler.domain_search,
        middlewares=[auth_required],
    )
    reg.add(
        "POST",
        "/search-by-project/{project_id}",
        handler.project_search,
        middlewares=[auth_required],
    )
    reg.add(
        "POST",
        "/search-by-role/{role_id}",
        handler.role_search,
        middlewares=[auth_required],
    )
    return reg
