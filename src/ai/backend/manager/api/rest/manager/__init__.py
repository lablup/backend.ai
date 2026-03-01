from __future__ import annotations

from typing import TYPE_CHECKING

from .registry import register_manager_api_module

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.routing import RouteRegistry
    from ai.backend.manager.services.processors import Processors

__all__ = ["register_manager_api_module"]


def register_routes(registry: RouteRegistry, processors: Processors | None = None) -> None:
    """Backward-compatible shim -- delegates to the old inline logic.

    The canonical entry-point is :func:`register_manager_api_module`; this wrapper
    exists only so that ``server.py`` keeps working until it is migrated to
    the new ``ModuleDeps`` convention.
    """
    from ai.backend.manager.api.rest.middleware.auth import superadmin_required

    from .handler import ManagerHandler

    if processors is None:
        raise RuntimeError("processors is required for manager module")
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
