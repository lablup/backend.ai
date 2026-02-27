"""New-style group config module using RouteRegistry and constructor DI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.manager import READ_ALLOWED, server_status_required
from ai.backend.manager.api.rest.middleware.auth import admin_required, auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import GroupConfigHandler

if TYPE_CHECKING:
    from ai.backend.manager.services.processors import Processors

_status_readable = server_status_required(READ_ALLOWED)


def register_routes(
    registry: RouteRegistry,
    processors: Processors,
) -> None:
    """Register group config routes on the given RouteRegistry."""
    handler = GroupConfigHandler(processors=processors)

    registry.add(
        "POST",
        "/group-config/dotfiles",
        handler.create,
        middlewares=[_status_readable, admin_required],
    )
    registry.add(
        "GET",
        "/group-config/dotfiles",
        handler.list_or_get,
        middlewares=[_status_readable, auth_required],
    )
    registry.add(
        "PATCH",
        "/group-config/dotfiles",
        handler.update,
        middlewares=[_status_readable, admin_required],
    )
    registry.add(
        "DELETE",
        "/group-config/dotfiles",
        handler.delete,
        middlewares=[_status_readable, admin_required],
    )
