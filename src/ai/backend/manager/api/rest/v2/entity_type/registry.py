"""Route registry for REST v2 entity type endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2EntityTypeHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_entity_type_routes(
    handler: V2EntityTypeHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 entity type routes and return the sub-registry."""
    registry = RouteRegistry.create("entity-types", route_deps.cors_options)

    registry.add(
        "GET",
        "",
        handler.list_entity_types,
        middlewares=[auth_required],
    )

    return registry
