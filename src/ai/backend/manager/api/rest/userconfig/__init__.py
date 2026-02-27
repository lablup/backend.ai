"""New-style user config module using RouteRegistry and constructor DI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.manager import READ_ALLOWED, server_status_required
from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import UserConfigHandler

if TYPE_CHECKING:
    from ai.backend.manager.services.processors import Processors

_status_readable = server_status_required(READ_ALLOWED)


def register_routes(
    registry: RouteRegistry,
    processors: Processors,
) -> None:
    """Register user config routes on the given RouteRegistry."""
    handler = UserConfigHandler(processors=processors)

    registry.add(
        "POST",
        "/user-config/dotfiles",
        handler.create,
        middlewares=[_status_readable, auth_required],
    )
    registry.add(
        "GET",
        "/user-config/dotfiles",
        handler.list_or_get,
        middlewares=[_status_readable, auth_required],
    )
    registry.add(
        "PATCH",
        "/user-config/dotfiles",
        handler.update,
        middlewares=[_status_readable, auth_required],
    )
    registry.add(
        "DELETE",
        "/user-config/dotfiles",
        handler.delete,
        middlewares=[_status_readable, auth_required],
    )
    registry.add(
        "POST",
        "/user-config/bootstrap-script",
        handler.update_bootstrap_script,
        middlewares=[_status_readable, auth_required],
    )
    registry.add(
        "GET",
        "/user-config/bootstrap-script",
        handler.get_bootstrap_script,
        middlewares=[_status_readable, auth_required],
    )
