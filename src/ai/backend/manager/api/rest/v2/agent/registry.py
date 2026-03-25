"""Route registration for v2 agent endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2AgentHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_agent_routes(
    handler: V2AgentHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all v2 agent routes."""
    reg = RouteRegistry.create("agents", route_deps.cors_options)
    reg.add("POST", "/search", handler.admin_search, middlewares=[superadmin_required])
    reg.add(
        "GET", "/total-resources", handler.get_total_resources, middlewares=[superadmin_required]
    )
    return reg
