from __future__ import annotations

from typing import TYPE_CHECKING

from .registry import register_container_registry_module

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.routing import RouteRegistry

__all__ = ["register_container_registry_module"]


def register_routes(registry: RouteRegistry) -> None:
    """Backward-compatible shim — delegates to the old inline logic.

    The canonical entry-point is :func:`register_container_registry_module`;
    this wrapper exists only so that ``server.py`` keeps working until it is
    migrated to the new ``ModuleDeps`` convention.
    """
    from ai.backend.manager.api.manager import ALL_ALLOWED, READ_ALLOWED, server_status_required
    from ai.backend.manager.api.rest.middleware.auth import superadmin_required

    from .handler import ContainerRegistryHandler

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
