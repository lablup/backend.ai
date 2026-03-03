"""Agent module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.server_status import ALL_ALLOWED, server_status_required

from .handler import AgentHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps


def register_agent_routes(deps: ModuleDeps) -> RouteRegistry:
    """Build the agent sub-application."""
    reg = RouteRegistry.create("agents", deps.cors_options)
    handler = AgentHandler(processors=deps.processors)

    reg.add(
        "POST",
        "/search",
        handler.search_agents,
        middlewares=[
            superadmin_required,
            server_status_required(ALL_ALLOWED, deps.config_provider),
        ],
    )
    return reg
