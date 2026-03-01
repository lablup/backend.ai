"""Container registry module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.manager import ALL_ALLOWED, READ_ALLOWED, server_status_required
from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import ContainerRegistryHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps


def register_container_registry_module(deps: ModuleDeps) -> RouteRegistry:
    """Build the container registry sub-application."""
    reg = RouteRegistry.create("container-registries", deps.cors_options)
    handler = ContainerRegistryHandler()

    reg.add(
        "PATCH",
        "/{registry_id}",
        handler.patch,
        middlewares=[server_status_required(READ_ALLOWED), superadmin_required],
    )
    reg.add(
        "POST",
        "/webhook/harbor",
        handler.harbor_webhook,
        middlewares=[server_status_required(ALL_ALLOWED)],
    )
    return reg
