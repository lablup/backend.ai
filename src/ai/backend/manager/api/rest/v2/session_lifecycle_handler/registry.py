"""Route registry for REST v2 session lifecycle handler endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.v2.session_lifecycle_handler.handler import (
    V2SessionLifecycleHandlerHandler,
)

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_session_lifecycle_handler_routes(
    handler: V2SessionLifecycleHandlerHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 session lifecycle handler routes and return the sub-registry."""
    registry = RouteRegistry.create("session-lifecycle-handlers", route_deps.cors_options)

    registry.add(
        "GET",
        "",
        handler.admin_list,
        middlewares=[superadmin_required],
    )

    return registry
