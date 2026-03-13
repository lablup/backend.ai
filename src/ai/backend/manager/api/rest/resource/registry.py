"""Resource module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import ResourceHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_resource_routes(handler: ResourceHandler, route_deps: RouteDeps) -> RouteRegistry:
    """Build the resource sub-application."""

    reg = RouteRegistry.create("resource", route_deps.cors_options)

    # Public preset listing (auth required)
    reg.add("GET", "/presets", handler.list_presets, middlewares=[auth_required])

    # Container registries (superadmin)
    reg.add(
        "GET",
        "/container-registries",
        handler.get_container_registries,
        middlewares=[superadmin_required],
    )

    # Check presets (auth required)
    reg.add("POST", "/check-presets", handler.check_presets, middlewares=[auth_required])

    # Recalculate usage (superadmin)
    reg.add(
        "POST",
        "/recalculate-usage",
        handler.recalculate_usage,
        middlewares=[superadmin_required],
    )

    # Usage statistics (superadmin)
    reg.add("GET", "/usage/month", handler.usage_per_month, middlewares=[superadmin_required])
    reg.add(
        "GET",
        "/usage/period",
        handler.usage_per_period,
        middlewares=[superadmin_required],
    )

    # User stats (auth required)
    reg.add("GET", "/stats/user/month", handler.user_month_stats, middlewares=[auth_required])

    # Admin stats (superadmin)
    reg.add(
        "GET",
        "/stats/admin/month",
        handler.admin_month_stats,
        middlewares=[superadmin_required],
    )

    # Watcher endpoints (superadmin)
    reg.add("GET", "/watcher", handler.get_watcher_status, middlewares=[superadmin_required])
    reg.add(
        "POST",
        "/watcher/agent/start",
        handler.watcher_agent_start,
        middlewares=[superadmin_required],
    )
    reg.add(
        "POST",
        "/watcher/agent/stop",
        handler.watcher_agent_stop,
        middlewares=[superadmin_required],
    )
    reg.add(
        "POST",
        "/watcher/agent/restart",
        handler.watcher_agent_restart,
        middlewares=[superadmin_required],
    )
    return reg
