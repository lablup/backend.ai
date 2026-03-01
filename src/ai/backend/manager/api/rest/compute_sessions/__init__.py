from __future__ import annotations

from typing import TYPE_CHECKING

from .registry import register_compute_sessions_module

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.routing import RouteRegistry
    from ai.backend.manager.services.processors import Processors

__all__ = ["register_compute_sessions_module"]


def register_routes(registry: RouteRegistry, processors: Processors) -> None:
    """Backward-compatible shim — delegates to the old inline logic.

    The canonical entry-point is :func:`register_compute_sessions_module`;
    this wrapper exists only so that ``server.py`` keeps working until it is
    migrated to the new ``ModuleDeps`` convention.
    """
    from ai.backend.manager.api.manager import ALL_ALLOWED, server_status_required
    from ai.backend.manager.api.rest.middleware.auth import superadmin_required

    from .handler import ComputeSessionsHandler

    handler = ComputeSessionsHandler(processors=processors)
    registry.add(
        "POST",
        "/search",
        handler.search_sessions,
        middlewares=[superadmin_required, server_status_required(ALL_ALLOWED)],
    )
