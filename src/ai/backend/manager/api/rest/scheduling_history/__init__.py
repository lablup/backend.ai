"""New-style scheduling history module using RouteRegistry and constructor DI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.manager import ALL_ALLOWED, server_status_required
from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import SchedulingHistoryHandler

if TYPE_CHECKING:
    from ai.backend.manager.services.processors import Processors


def register_routes(
    registry: RouteRegistry,
    processors: Processors,
) -> None:
    """Register scheduling history routes on the given RouteRegistry."""
    handler = SchedulingHistoryHandler(processors=processors)

    registry.add(
        "POST",
        "/scheduling-history/sessions/search",
        handler.search_session_history,
        middlewares=[superadmin_required, server_status_required(ALL_ALLOWED)],
    )
    registry.add(
        "POST",
        "/scheduling-history/deployments/search",
        handler.search_deployment_history,
        middlewares=[superadmin_required, server_status_required(ALL_ALLOWED)],
    )
    registry.add(
        "POST",
        "/scheduling-history/routes/search",
        handler.search_route_history,
        middlewares=[superadmin_required, server_status_required(ALL_ALLOWED)],
    )
