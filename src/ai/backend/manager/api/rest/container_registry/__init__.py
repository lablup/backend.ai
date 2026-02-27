"""New-style container_registry module using RouteRegistry."""

from __future__ import annotations

from ai.backend.manager.api.manager import ALL_ALLOWED, READ_ALLOWED, server_status_required
from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import ContainerRegistryHandler


def register_routes(registry: RouteRegistry) -> None:
    """Register container-registry routes on the given RouteRegistry."""
    handler = ContainerRegistryHandler()

    registry.add(
        "PATCH",
        "/{registry_id}",
        handler.patch,
        middlewares=[server_status_required(READ_ALLOWED), superadmin_required],
    )
    registry.add(
        "POST",
        "/webhook/harbor",
        handler.harbor_webhook,
        middlewares=[server_status_required(ALL_ALLOWED)],
    )
