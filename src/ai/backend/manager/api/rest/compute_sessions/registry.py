"""Compute sessions module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import ComputeSessionsHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_compute_sessions_routes(
    handler: ComputeSessionsHandler, route_deps: RouteDeps
) -> RouteRegistry:
    """Build the compute sessions sub-application."""
    reg = RouteRegistry.create("compute-sessions", route_deps.cors_options)

    reg.add(
        "POST",
        "/search",
        handler.search_sessions,
        middlewares=[
            superadmin_required,
            route_deps.all_status_mw,
        ],
    )
    return reg
