"""New-style compute sessions module using RouteRegistry and constructor DI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.manager import ALL_ALLOWED, server_status_required
from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import ComputeSessionsHandler

if TYPE_CHECKING:
    from ai.backend.manager.services.processors import Processors


def register_routes(
    registry: RouteRegistry,
    processors: Processors,
) -> None:
    """Register compute sessions routes on the given RouteRegistry."""
    handler = ComputeSessionsHandler(processors=processors)

    registry.add(
        "POST",
        "/compute-sessions/search",
        handler.search_sessions,
        middlewares=[superadmin_required, server_status_required(ALL_ALLOWED)],
    )
