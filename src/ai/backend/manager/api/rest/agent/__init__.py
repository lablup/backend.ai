"""New-style agent module using RouteRegistry and constructor DI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.manager import ALL_ALLOWED, server_status_required
from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import AgentHandler

if TYPE_CHECKING:
    from ai.backend.manager.services.processors import Processors


def register_routes(
    registry: RouteRegistry,
    processors: Processors,
) -> None:
    """Register agent routes on the given RouteRegistry."""
    handler = AgentHandler(processors=processors)

    registry.add(
        "POST",
        "/search",
        handler.search_agents,
        middlewares=[superadmin_required, server_status_required(ALL_ALLOWED)],
    )
