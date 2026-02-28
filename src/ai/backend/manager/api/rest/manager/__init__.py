"""New-style manager module using RouteRegistry and constructor DI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import ManagerHandler

if TYPE_CHECKING:
    from ai.backend.manager.services.processors import Processors


def register_routes(
    registry: RouteRegistry,
    processors: Processors,
) -> None:
    """Register manager routes on the given RouteRegistry."""
    handler = ManagerHandler(processors=processors)

    # Public endpoints (no auth required)
    registry.add("GET", "/status", handler.fetch_manager_status)
    registry.add("GET", "/announcement", handler.get_announcement)
    registry.add("GET", "/prom", handler.get_manager_status_for_prom)

    # Superadmin endpoints
    registry.add("PUT", "/status", handler.update_manager_status, middlewares=[superadmin_required])
    registry.add(
        "POST",
        "/announcement",
        handler.update_announcement,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/scheduler/operation",
        handler.perform_scheduler_ops,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/scheduler/trigger",
        handler.scheduler_trigger,
        middlewares=[superadmin_required],
    )
    registry.add(
        "GET",
        "/scheduler/status",
        handler.scheduler_healthcheck,
        middlewares=[superadmin_required],
    )
