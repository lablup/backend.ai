"""Agent module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import AgentHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_agent_routes(handler: AgentHandler, route_deps: RouteDeps) -> RouteRegistry:
    """Build the agent sub-application."""
    reg = RouteRegistry.create("agents", route_deps.cors_options)

    reg.add(
        "POST",
        "/search",
        handler.search_agents,
        middlewares=[
            superadmin_required,
            route_deps.all_status_mw,
        ],
    )
    return reg
