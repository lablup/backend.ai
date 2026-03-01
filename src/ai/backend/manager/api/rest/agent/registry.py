"""Agent module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.manager import ALL_ALLOWED, server_status_required
from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import AgentHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps


def register_agent_routes(deps: ModuleDeps) -> RouteRegistry:
    """Build the agent sub-application."""
    reg = RouteRegistry.create("agents", deps.cors_options)
    if deps.processors is None:
        raise RuntimeError("processors is required for agent module")
    handler = AgentHandler(processors=deps.processors)

    reg.add(
        "POST",
        "/search",
        handler.search_agents,
        middlewares=[superadmin_required, server_status_required(ALL_ALLOWED)],
    )
    return reg
