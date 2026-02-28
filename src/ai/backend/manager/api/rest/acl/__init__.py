"""New-style ACL module using RouteRegistry and constructor DI."""

from __future__ import annotations

from ai.backend.manager.api.manager import ALL_ALLOWED, server_status_required
from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import AclHandler


def register_routes(
    registry: RouteRegistry,
) -> None:
    """Register ACL routes on the given RouteRegistry."""
    handler = AclHandler()

    registry.add(
        "GET",
        "/acl",
        handler.get_permission,
        middlewares=[auth_required, server_status_required(ALL_ALLOWED)],
    )
