"""New-style domain config module using RouteRegistry and constructor DI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import admin_required, auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import DomainConfigHandler

if TYPE_CHECKING:
    from ai.backend.manager.services.processors import Processors


def register_routes(
    registry: RouteRegistry,
    processors: Processors,
) -> None:
    """Register domain config routes on the given RouteRegistry."""
    handler = DomainConfigHandler(processors=processors)

    registry.add("POST", "/domain-config/dotfiles", handler.create, middlewares=[admin_required])
    registry.add("GET", "/domain-config/dotfiles", handler.list_or_get, middlewares=[auth_required])
    registry.add("PATCH", "/domain-config/dotfiles", handler.update, middlewares=[admin_required])
    registry.add("DELETE", "/domain-config/dotfiles", handler.delete, middlewares=[admin_required])
