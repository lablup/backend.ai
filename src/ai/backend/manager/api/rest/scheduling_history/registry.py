"""Scheduling history module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps
    from ai.backend.manager.services.processors import Processors


def register_routes(
    registry: RouteRegistry,
    processors: Processors,
) -> None:
    """Register scheduling history routes on the given RouteRegistry (legacy API)."""
    from .handler import SchedulingHistoryHandler

    handler = SchedulingHistoryHandler(processors=processors)

    registry.add(
        "POST",
        "/sessions/search",
        handler.search_session_history,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/deployments/search",
        handler.search_deployment_history,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/routes/search",
        handler.search_route_history,
        middlewares=[superadmin_required],
    )


def register_scheduling_history_module(deps: ModuleDeps) -> RouteRegistry:
    """Build the scheduling history sub-application."""
    # Import handler inside function to avoid circular imports
    from .handler import SchedulingHistoryHandler

    reg = RouteRegistry.create("scheduling-history", deps.cors_options)
    if deps.processors is None:
        raise RuntimeError("processors is required for scheduling_history module")
    handler = SchedulingHistoryHandler(processors=deps.processors)

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
