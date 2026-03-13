"""Group config module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import admin_required, auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import GroupConfigHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_groupconfig_routes(
    handler: GroupConfigHandler, route_deps: RouteDeps
) -> RouteRegistry:
    """Build the group config sub-application."""

    reg = RouteRegistry.create("group-config", route_deps.cors_options)
    _status_readable = route_deps.read_status_mw

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
