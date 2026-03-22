"""Health module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import HealthHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_health_routes(
    handler: HealthHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Build the health sub-application."""
    reg = RouteRegistry.create("health", route_deps.cors_options)

    # Public endpoint — no auth required
    reg.add("GET", "", handler.hello)

    return reg
