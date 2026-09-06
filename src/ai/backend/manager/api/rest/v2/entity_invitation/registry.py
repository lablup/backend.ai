"""Route registry for the REST v2 entity invitation endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2EntityInvitationHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_entity_invitation_routes(
    handler: V2EntityInvitationHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    registry = RouteRegistry.create("entity-invitations", route_deps.cors_options)

    registry.add("POST", "", handler.create, middlewares=[auth_required])
    registry.add("GET", "/{invitation_id}", handler.get, middlewares=[auth_required])
    registry.add("POST", "/{invitation_id}/accept", handler.accept, middlewares=[auth_required])
    registry.add("POST", "/{invitation_id}/reject", handler.reject, middlewares=[auth_required])
    registry.add("DELETE", "/{invitation_id}", handler.cancel, middlewares=[auth_required])
    registry.add("POST", "/scoped/search", handler.scoped_search, middlewares=[auth_required])

    return registry
