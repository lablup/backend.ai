"""Route registry for REST v2 label endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2EntityLabelHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_entity_label_routes(
    handler: V2EntityLabelHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 label routes and return the sub-registry.

    Behind `auth_required` rather than an admin gate: every operation is checked against
    the labeled entity, so what a caller may reach is what RBAC already gives them.
    """
    registry = RouteRegistry.create("entity-labels", route_deps.cors_options)

    registry.add("PUT", "", handler.upsert_label, middlewares=[auth_required])
    registry.add("DELETE", "/{label_id}", handler.purge_label, middlewares=[auth_required])
    registry.add("POST", "/search", handler.search_labels, middlewares=[auth_required])

    return registry
