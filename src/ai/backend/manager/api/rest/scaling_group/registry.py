"""Scaling group module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.manager import READ_ALLOWED, server_status_required
from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps


def register_routes(
    registry: RouteRegistry,
) -> None:
    """Register scaling group routes on the given RouteRegistry (legacy API)."""
    from .handler import ScalingGroupHandler

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


def register_scaling_group_module(deps: ModuleDeps) -> RouteRegistry:
    """Build the scaling group sub-application."""
    # Import handler inside function to avoid circular imports
    from .handler import ScalingGroupHandler

    reg = RouteRegistry.create("scaling-groups", deps.cors_options)
    handler = ScalingGroupHandler()

    reg.add(
        "GET",
        "",
        handler.list_available_sgroups,
        middlewares=[auth_required, server_status_required(READ_ALLOWED)],
    )
    reg.add(
        "GET",
        "/{scaling_group}/wsproxy-version",
        handler.get_wsproxy_version,
        middlewares=[auth_required, server_status_required(READ_ALLOWED)],
    )
    return reg
