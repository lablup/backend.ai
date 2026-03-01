from __future__ import annotations

from typing import TYPE_CHECKING

from .registry import register_domain_routes

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.routing import RouteRegistry
    from ai.backend.manager.services.processors import Processors

__all__ = ["register_domain_routes"]


def register_routes(registry: RouteRegistry, processors: Processors) -> None:
    """Backward-compatible shim — delegates to the old inline logic.

    The canonical entry-point is :func:`register_domain_routes`; this wrapper
    exists only so that ``server.py`` keeps working until it is migrated to
    the new ``ModuleDeps`` convention.
    """
    from ai.backend.manager.api.rest.middleware.auth import superadmin_required

    from .handler import DomainHandler

    handler = DomainHandler(processors=processors)

    registry.add("POST", "", handler.create, middlewares=[superadmin_required])
    registry.add(
        "GET",
        r"/{domain_name}",
        handler.get,
        middlewares=[superadmin_required],
    )
    registry.add("POST", "/search", handler.search, middlewares=[superadmin_required])
    registry.add(
        "PATCH",
        r"/{domain_name}",
        handler.update,
        middlewares=[superadmin_required],
    )
    registry.add("POST", "/delete", handler.delete, middlewares=[superadmin_required])
    registry.add("POST", "/purge", handler.purge, middlewares=[superadmin_required])
