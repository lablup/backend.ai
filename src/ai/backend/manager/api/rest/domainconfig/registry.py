"""Domain config module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.manager import READ_ALLOWED, server_status_required
from ai.backend.manager.api.rest.middleware.auth import admin_required, auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps
    from ai.backend.manager.services.processors import Processors

_status_readable = server_status_required(READ_ALLOWED)


def register_routes(
    registry: RouteRegistry,
    processors: Processors,
) -> None:
    """Register domain config routes on the given RouteRegistry (legacy API)."""
    from .handler import DomainConfigHandler

    handler = DomainConfigHandler(processors=processors)

    registry.add(
        "POST",
        "/dotfiles",
        handler.create,
        middlewares=[_status_readable, admin_required],
    )
    registry.add(
        "GET",
        "/dotfiles",
        handler.list_or_get,
        middlewares=[_status_readable, auth_required],
    )
    registry.add(
        "PATCH",
        "/dotfiles",
        handler.update,
        middlewares=[_status_readable, admin_required],
    )
    registry.add(
        "DELETE",
        "/dotfiles",
        handler.delete,
        middlewares=[_status_readable, admin_required],
    )


def register_domainconfig_module(deps: ModuleDeps) -> RouteRegistry:
    """Build the domain config sub-application."""
    # Import handler inside function to avoid circular imports
    from .handler import DomainConfigHandler

    reg = RouteRegistry.create("domain-config", deps.cors_options)
    handler = DomainConfigHandler(processors=deps.processors)

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
