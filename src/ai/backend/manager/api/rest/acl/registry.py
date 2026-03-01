"""ACL module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.manager import ALL_ALLOWED, server_status_required
from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import AclHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps


def register_acl_routes(deps: ModuleDeps) -> RouteRegistry:
    """Build the ACL sub-application."""
    reg = RouteRegistry.create("acl", deps.cors_options)
    handler = AclHandler()

    reg.add(
        "GET",
        "",
        handler.get_permission,
        middlewares=[auth_required, server_status_required(ALL_ALLOWED)],
    )
    return reg
