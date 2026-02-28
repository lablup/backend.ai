"""New-style group module using RouteRegistry and constructor DI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import GroupHandler

if TYPE_CHECKING:
    from ai.backend.manager.service.base import ServicesContext


def register_routes(
    registry: RouteRegistry,
    services_ctx: ServicesContext,
) -> None:
    """Register group routes on the given RouteRegistry."""
    handler = GroupHandler(services_ctx=services_ctx)

    registry.add(
        "POST",
        "/registry-quota",
        handler.create_registry_quota,
        middlewares=[superadmin_required],
    )
    registry.add(
        "GET",
        "/registry-quota",
        handler.read_registry_quota,
        middlewares=[superadmin_required],
    )
    registry.add(
        "PATCH",
        "/registry-quota",
        handler.update_registry_quota,
        middlewares=[superadmin_required],
    )
    registry.add(
        "DELETE",
        "/registry-quota",
        handler.delete_registry_quota,
        middlewares=[superadmin_required],
    )
