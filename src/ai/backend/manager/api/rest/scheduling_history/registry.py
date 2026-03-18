"""Scheduling history module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import SchedulingHistoryHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_scheduling_history_routes(
    handler: SchedulingHistoryHandler, route_deps: RouteDeps
) -> RouteRegistry:
    """Build the scheduling history sub-application."""

    reg = RouteRegistry.create("scheduling-history", route_deps.cors_options)

    reg.add(
        "POST",
        "/sessions/search",
        handler.search_session_history,
        middlewares=[superadmin_required],
    )
    reg.add(
        "POST",
        "/deployments/search",
        handler.search_deployment_history,
        middlewares=[superadmin_required],
    )
    reg.add(
        "POST",
        "/routes/search",
        handler.search_route_history,
        middlewares=[superadmin_required],
    )
    return reg
