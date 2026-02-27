"""New-style error log module using RouteRegistry and constructor DI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.manager import READ_ALLOWED, server_status_required
from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import ErrorLogHandler

if TYPE_CHECKING:
    from ai.backend.manager.services.processors import Processors


def register_routes(
    registry: RouteRegistry,
    processors: Processors,
) -> None:
    """Register error log routes on the given RouteRegistry."""
    handler = ErrorLogHandler(processors=processors)

    registry.add(
        "POST",
        "/logs/error",
        handler.append,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )
    registry.add(
        "GET",
        "/logs/error",
        handler.list_logs,
        middlewares=[auth_required, server_status_required(READ_ALLOWED)],
    )
    registry.add(
        "POST",
        "/logs/error/{log_id}/clear",
        handler.mark_cleared,
        middlewares=[auth_required, server_status_required(READ_ALLOWED)],
    )
