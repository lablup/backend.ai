"""Route registry for the REST v2 entity invitation endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2EntityShareHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_entity_share_routes(
    handler: V2EntityShareHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    registry = RouteRegistry.create("entity-shares", route_deps.cors_options)

    registry.add("POST", "", handler.create, middlewares=[auth_required])
    registry.add("GET", "/{share_id}", handler.get, middlewares=[auth_required])
    registry.add("POST", "/{share_id}/accept", handler.accept, middlewares=[auth_required])
    registry.add("POST", "/{share_id}/reject", handler.reject, middlewares=[auth_required])
    registry.add("DELETE", "/{share_id}", handler.cancel, middlewares=[auth_required])
    registry.add("POST", "/scoped/search", handler.scoped_search, middlewares=[auth_required])

    return registry
