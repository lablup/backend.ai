"""Group config module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.manager import READ_ALLOWED, server_status_required
from ai.backend.manager.api.rest.middleware.auth import admin_required, auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps

_status_readable = server_status_required(READ_ALLOWED)


def register_groupconfig_routes(deps: ModuleDeps) -> RouteRegistry:
    """Build the group config sub-application."""
    # Import handler inside function to avoid circular imports
    from .handler import GroupConfigHandler

    reg = RouteRegistry.create("group-config", deps.cors_options)
    handler = GroupConfigHandler(processors=deps.processors)

    reg.add(
        "POST",
        "/dotfiles",
        handler.create,
        middlewares=[_status_readable, admin_required],
    )
    reg.add(
        "GET",
        "/dotfiles",
        handler.list_or_get,
        middlewares=[_status_readable, auth_required],
    )
    reg.add(
        "PATCH",
        "/dotfiles",
        handler.update,
        middlewares=[_status_readable, admin_required],
    )
    reg.add(
        "DELETE",
        "/dotfiles",
        handler.delete,
        middlewares=[_status_readable, admin_required],
    )
    return reg
