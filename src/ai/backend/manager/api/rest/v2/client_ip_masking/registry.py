"""Route registry for REST v2 client IP masking endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2ClientIPMaskingHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_client_ip_masking_routes(
    handler: V2ClientIPMaskingHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 client IP masking routes and return the sub-registry."""
    registry = RouteRegistry.create("client-ip-masking-policies", route_deps.cors_options)

    registry.add("POST", "/search", handler.admin_search, middlewares=[superadmin_required])
    registry.add("POST", "/upsert", handler.admin_upsert, middlewares=[superadmin_required])
    registry.add("POST", "/purge", handler.admin_purge, middlewares=[superadmin_required])

    return registry
