"""Group module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps


def register_group_routes(deps: ModuleDeps) -> RouteRegistry:
    """Build the group sub-application."""
    # Import handler inside function to avoid circular imports
    from .handler import GroupHandler

    reg = RouteRegistry.create("group", deps.cors_options)
    handler = GroupHandler(processors=deps.processors)

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
