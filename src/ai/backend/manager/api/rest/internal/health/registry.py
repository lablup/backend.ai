"""Internal health module registrar."""

from __future__ import annotations

from ai.backend.manager.api.rest.internal.health.handler import InternalHealthHandler
from ai.backend.manager.api.rest.routing import RouteRegistry


def register_internal_health_routes(handler: InternalHealthHandler) -> RouteRegistry:
    """Build the internal health sub-application."""
    reg = RouteRegistry.create("health", {})

    # Internal endpoint — no CORS required
    reg.add("GET", "", handler.hello)

    return reg
