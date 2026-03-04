"""Health module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.routing import RouteRegistry

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps


def register_health_routes(deps: ModuleDeps) -> RouteRegistry:
    """Build the health sub-application."""
    from .handler import HealthHandler

    reg = RouteRegistry.create("health", deps.cors_options)

    if deps.health_probe is None:
        raise RuntimeError("health_probe is required for the health module")

    handler = HealthHandler(health_probe=deps.health_probe)

    # Public endpoint — no auth required
    reg.add("GET", "", handler.hello)

    return reg
