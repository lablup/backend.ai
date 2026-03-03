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
from ai.backend.manager.api.rest.server_status import READ_ALLOWED, server_status_required

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps


def register_error_log_routes(deps: ModuleDeps) -> RouteRegistry:
    """Build the error log sub-application."""
    from .handler import ErrorLogHandler

    reg = RouteRegistry.create("logs", deps.cors_options)
    handler = ErrorLogHandler(processors=deps.processors)

    reg.add(
        "POST",
        "/error",
        handler.append,
        middlewares=[server_status_required(READ_ALLOWED, deps.config_provider), auth_required],
    )
    reg.add(
        "GET",
        "/error",
        handler.list_logs,
        middlewares=[auth_required, server_status_required(READ_ALLOWED, deps.config_provider)],
    )
    reg.add(
        "POST",
        "/error/{log_id}/clear",
        handler.mark_cleared,
        middlewares=[auth_required, server_status_required(READ_ALLOWED, deps.config_provider)],
    )
    return reg
