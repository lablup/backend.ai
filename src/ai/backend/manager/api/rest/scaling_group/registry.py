"""Scaling group module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import ScalingGroupHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_scaling_group_routes(
    handler: ScalingGroupHandler, route_deps: RouteDeps
) -> RouteRegistry:
    """Build the scaling group sub-application."""

    reg = RouteRegistry.create("scaling-groups", route_deps.cors_options)

    reg.add(
        "GET",
        "",
        handler.list_available_sgroups,
        middlewares=[auth_required, route_deps.read_status_mw],
    )
    reg.add(
        "GET",
        "/{scaling_group}/wsproxy-version",
        handler.get_wsproxy_version,
        middlewares=[auth_required, route_deps.read_status_mw],
    )
    return reg
