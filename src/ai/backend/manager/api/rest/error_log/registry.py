"""Error log module registrar.

Lifecycle management (GlobalTimer for log cleanup, event dispatcher
integration) is handled by the DependencyComposer:

* Event consumer: ``event_dispatcher.handlers.log_cleanup``
* GlobalTimer: ``dependencies.processing.log_cleanup_timer``
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import ErrorLogHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_error_log_routes(handler: ErrorLogHandler, route_deps: RouteDeps) -> RouteRegistry:
    """Build the error log sub-application."""

    reg = RouteRegistry.create("logs", route_deps.cors_options)

    reg.add(
        "POST",
        "/error",
        handler.append,
        middlewares=[route_deps.read_status_mw, auth_required],
    )
    reg.add(
        "GET",
        "/error",
        handler.list_logs,
        middlewares=[auth_required, route_deps.read_status_mw],
    )
    reg.add(
        "POST",
        "/error/{log_id}/clear",
        handler.mark_cleared,
        middlewares=[auth_required, route_deps.read_status_mw],
    )
    return reg
