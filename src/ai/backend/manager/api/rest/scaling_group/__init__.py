"""New-style scaling group module using RouteRegistry and constructor DI."""

from __future__ import annotations

from ai.backend.manager.api.manager import READ_ALLOWED, server_status_required
from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import ScalingGroupHandler


def register_routes(
    registry: RouteRegistry,
) -> None:
    """Register scaling group routes on the given RouteRegistry."""
    handler = ScalingGroupHandler()

    registry.add(
        "GET",
        "",
        handler.list_available_sgroups,
        middlewares=[auth_required, server_status_required(READ_ALLOWED)],
    )
    registry.add(
        "GET",
        "/{scaling_group}/wsproxy-version",
        handler.get_wsproxy_version,
        middlewares=[auth_required, server_status_required(READ_ALLOWED)],
    )
