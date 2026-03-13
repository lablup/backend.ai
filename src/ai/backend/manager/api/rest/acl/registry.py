"""ACL module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import AclHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_acl_routes(handler: AclHandler, route_deps: RouteDeps) -> RouteRegistry:
    """Build the ACL sub-application."""
    reg = RouteRegistry.create("acl", route_deps.cors_options)

    reg.add(
        "GET",
        "",
        handler.get_permission,
        middlewares=[auth_required, route_deps.all_status_mw],
    )
    return reg
