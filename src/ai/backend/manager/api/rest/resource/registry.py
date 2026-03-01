"""Resource module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps
    from ai.backend.manager.services.processors import Processors


def register_routes(
    registry: RouteRegistry,
    processors: Processors,
) -> None:
    """Register resource routes on the given RouteRegistry (legacy API)."""
    from .handler import ResourceHandler

    handler = ResourceHandler(processors=processors)

    # Public preset listing (auth required)
    registry.add("GET", "/presets", handler.list_presets, middlewares=[auth_required])

    # Container registries (superadmin)
    registry.add(
        "GET",
        "/container-registries",
        handler.get_container_registries,
        middlewares=[superadmin_required],
    )

    # Check presets (auth required)
    registry.add("POST", "/check-presets", handler.check_presets, middlewares=[auth_required])

    # Recalculate usage (superadmin)
    registry.add(
        "POST",
        "/recalculate-usage",
        handler.recalculate_usage,
        middlewares=[superadmin_required],
    )

    # Usage statistics (superadmin)
    registry.add("GET", "/usage/month", handler.usage_per_month, middlewares=[superadmin_required])
    registry.add(
        "GET",
        "/usage/period",
        handler.usage_per_period,
        middlewares=[superadmin_required],
    )

    # User stats (auth required)
    registry.add("GET", "/stats/user/month", handler.user_month_stats, middlewares=[auth_required])

    # Admin stats (superadmin)
    registry.add(
        "GET",
        "/stats/admin/month",
        handler.admin_month_stats,
        middlewares=[superadmin_required],
    )

    # Watcher endpoints (superadmin)
    registry.add("GET", "/watcher", handler.get_watcher_status, middlewares=[superadmin_required])
    registry.add(
        "POST",
        "/watcher/agent/start",
        handler.watcher_agent_start,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/watcher/agent/stop",
        handler.watcher_agent_stop,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/watcher/agent/restart",
        handler.watcher_agent_restart,
        middlewares=[superadmin_required],
    )


def register_resource_module(deps: ModuleDeps) -> RouteRegistry:
    """Build the resource sub-application."""
    # Import handler inside function to avoid circular imports
    from .handler import ResourceHandler

    reg = RouteRegistry.create("resource", deps.cors_options)
    if deps.processors is None:
        raise RuntimeError("processors is required for resource module")
    handler = ResourceHandler(processors=deps.processors)

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
