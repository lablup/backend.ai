"""Route registry for REST v2 scope operation endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2ScopeOperationHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_scope_operation_routes(
    handler: V2ScopeOperationHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 scope operation routes and return the sub-registry."""
    registry = RouteRegistry.create("scope-operations", route_deps.cors_options)

    registry.add(
        "GET",
        "",
        handler.list_scope_operations,
        middlewares=[auth_required],
    )

    return registry
