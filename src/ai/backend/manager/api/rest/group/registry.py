"""Group module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps
    from ai.backend.manager.service.base import ServicesContext


def register_routes(
    registry: RouteRegistry,
    services_ctx: ServicesContext,
) -> None:
    """Register group routes on the given RouteRegistry (legacy API)."""
    from .handler import GroupHandler

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


def register_group_module(deps: ModuleDeps) -> RouteRegistry:
    """Build the group sub-application."""
    # Import handler inside function to avoid circular imports
    from .handler import GroupHandler

    reg = RouteRegistry.create("group", deps.cors_options)
    if deps.services_ctx is None:
        raise RuntimeError("services_ctx is required for group module")
    handler = GroupHandler(services_ctx=deps.services_ctx)

    reg.add(
        "POST",
        "/registry-quota",
        handler.create_registry_quota,
        middlewares=[superadmin_required],
    )
    reg.add(
        "GET",
        "/registry-quota",
        handler.read_registry_quota,
        middlewares=[superadmin_required],
    )
    reg.add(
        "PATCH",
        "/registry-quota",
        handler.update_registry_quota,
        middlewares=[superadmin_required],
    )
    reg.add(
        "DELETE",
        "/registry-quota",
        handler.delete_registry_quota,
        middlewares=[superadmin_required],
    )
    return reg
