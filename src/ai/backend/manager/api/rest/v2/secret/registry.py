"""Route registration for v2 secret endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2SecretHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_secret_routes(
    handler: V2SecretHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register v2 secret routes, all of them superadmin-only."""
    reg = RouteRegistry.create("secrets", route_deps.cors_options)
    reg.add("POST", "/reencrypt", handler.admin_reencrypt, middlewares=[superadmin_required])
    reg.add("GET", "/status", handler.admin_status, middlewares=[superadmin_required])
    return reg
