"""Domain sub-registry registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import DomainHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps


def register_domain_routes(deps: ModuleDeps) -> RouteRegistry:
    """Build the domain sub-registry (child of admin)."""
    reg = RouteRegistry.create("domains", deps.cors_options)
    handler = DomainHandler(processors=deps.processors)

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
