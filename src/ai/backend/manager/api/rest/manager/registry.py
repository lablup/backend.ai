"""Manager API module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import ManagerHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_manager_api_routes(handler: ManagerHandler, route_deps: RouteDeps) -> RouteRegistry:
    """Build the manager sub-application."""

    reg = RouteRegistry.create("manager", route_deps.cors_options)

    # Public endpoints (no auth required)
    reg.add("GET", "/status", handler.fetch_manager_status)
    reg.add("GET", "/announcement", handler.get_announcement)
    reg.add("GET", "/prom", handler.get_manager_status_for_prom)

    # Superadmin endpoints
    reg.add("PUT", "/status", handler.update_manager_status, middlewares=[superadmin_required])
    reg.add(
        "POST",
        "/announcement",
        handler.update_announcement,
        middlewares=[superadmin_required],
    )
    reg.add(
        "POST",
        "/scheduler/operation",
        handler.perform_scheduler_ops,
        middlewares=[superadmin_required],
    )
    reg.add(
        "POST",
        "/scheduler/trigger",
        handler.scheduler_trigger,
        middlewares=[superadmin_required],
    )
    reg.add(
        "GET",
        "/scheduler/status",
        handler.scheduler_healthcheck,
        middlewares=[superadmin_required],
    )
    return reg
