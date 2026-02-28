"""New-style domain module using RouteRegistry and constructor DI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import DomainHandler

if TYPE_CHECKING:
    from ai.backend.manager.services.processors import Processors


def register_routes(
    registry: RouteRegistry,
    processors: Processors,
) -> None:
    """Register domain routes on the given RouteRegistry."""
    handler = DomainHandler(processors=processors)

    registry.add("POST", "/admin/domains", handler.create, middlewares=[superadmin_required])
    registry.add(
        "GET",
        r"/admin/domains/{domain_name}",
        handler.get,
        middlewares=[superadmin_required],
    )
    registry.add("POST", "/admin/domains/search", handler.search, middlewares=[superadmin_required])
    registry.add(
        "PATCH",
        r"/admin/domains/{domain_name}",
        handler.update,
        middlewares=[superadmin_required],
    )
    registry.add("POST", "/admin/domains/delete", handler.delete, middlewares=[superadmin_required])
    registry.add("POST", "/admin/domains/purge", handler.purge, middlewares=[superadmin_required])
