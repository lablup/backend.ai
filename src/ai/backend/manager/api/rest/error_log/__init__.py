from __future__ import annotations

from typing import TYPE_CHECKING

from .registry import register_error_log_module

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.routing import RouteRegistry
    from ai.backend.manager.services.processors import Processors

__all__ = ["register_error_log_module"]


def register_routes(registry: RouteRegistry, processors: Processors | None = None) -> None:
    """Backward-compatible shim -- delegates to the old inline logic.

    The canonical entry-point is :func:`register_error_log_module`; this wrapper
    exists only so that ``server.py`` keeps working until it is migrated to
    the new ``ModuleDeps`` convention.
    """
    from ai.backend.manager.api.manager import READ_ALLOWED, server_status_required
    from ai.backend.manager.api.rest.middleware.auth import auth_required

    from .handler import ErrorLogHandler

    if processors is None:
        raise RuntimeError("processors is required for error_log module")
    handler = ErrorLogHandler(processors=processors)

    registry.add(
        "POST",
        "/error",
        handler.append,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )
    registry.add(
        "GET",
        "/error",
        handler.list_logs,
        middlewares=[auth_required, server_status_required(READ_ALLOWED)],
    )
    registry.add(
        "POST",
        "/error/{log_id}/clear",
        handler.mark_cleared,
        middlewares=[auth_required, server_status_required(READ_ALLOWED)],
    )
