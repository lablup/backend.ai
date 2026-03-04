"""Manager API module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps


def register_manager_api_routes(deps: ModuleDeps) -> RouteRegistry:
    """Build the manager sub-application."""
    from .handler import ManagerHandler

    reg = RouteRegistry.create("manager", deps.cors_options)
    handler = ManagerHandler(processors=deps.processors)

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
