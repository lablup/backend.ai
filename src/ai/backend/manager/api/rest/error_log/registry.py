"""Error log module registrar.

Old ``error_logs`` rows are purged by the DB record retention sweep under the
``logs`` category (BEP-1063); this module only registers the HTTP routes. A
manual immediate sweep can be triggered via the ``clear-history`` CLI.
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
