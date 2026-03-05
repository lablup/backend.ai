"""Domain sub-registry registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import DomainHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_domain_routes(handler: DomainHandler, route_deps: RouteDeps) -> RouteRegistry:
    """Build the domain sub-registry (child of admin)."""
    reg = RouteRegistry.create("domains", route_deps.cors_options)

    reg.add("POST", "", handler.create, middlewares=[superadmin_required])
    reg.add(
        "GET",
        r"/{domain_name}",
        handler.get,
        middlewares=[superadmin_required],
    )
    reg.add("POST", "/search", handler.search, middlewares=[superadmin_required])
    reg.add(
        "PATCH",
        r"/{domain_name}",
        handler.update,
        middlewares=[superadmin_required],
    )
    reg.add("POST", "/delete", handler.delete, middlewares=[superadmin_required])
    reg.add("POST", "/purge", handler.purge, middlewares=[superadmin_required])

    return reg
