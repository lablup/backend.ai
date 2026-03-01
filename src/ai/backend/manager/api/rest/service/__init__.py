from __future__ import annotations

from typing import TYPE_CHECKING

from .registry import register_service_module

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.routing import RouteRegistry
    from ai.backend.manager.services.processors import Processors

__all__ = ["register_service_module"]


def register_routes(registry: RouteRegistry, processors: Processors | None = None) -> None:
    """Backward-compatible shim -- delegates to the old inline logic.

    The canonical entry-point is :func:`register_service_module`; this wrapper
    exists only so that ``server.py`` keeps working until it is migrated to
    the new ``ModuleDeps`` convention.
    """
    from ai.backend.manager.api.rest.middleware.auth import auth_required

    from .handler import ServiceHandler

    if processors is None:
        raise RuntimeError("processors is required for service module")
    handler = ServiceHandler(processors=processors)

    # Service list & create (root)
    registry.add("GET", "", handler.list_serve, middlewares=[auth_required])
    registry.add("POST", "", handler.create, middlewares=[auth_required])

    # Search & utilities
    registry.add("POST", "/_/search", handler.search_services, middlewares=[auth_required])
    registry.add("POST", "/_/try", handler.try_start, middlewares=[auth_required])
    registry.add(
        "GET",
        "/_/runtimes",
        handler.list_supported_runtimes,
        middlewares=[auth_required],
    )

    # Per-service endpoints
    registry.add("GET", "/{service_id}", handler.get_info, middlewares=[auth_required])
    registry.add("DELETE", "/{service_id}", handler.delete, middlewares=[auth_required])
    registry.add(
        "GET",
        "/{service_id}/errors",
        handler.list_errors,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/{service_id}/errors/clear",
        handler.clear_error,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/{service_id}/scale",
        handler.scale,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/{service_id}/sync",
        handler.sync,
        middlewares=[auth_required],
    )
    registry.add(
        "PUT",
        "/{service_id}/routings/{route_id}",
        handler.update_route,
        middlewares=[auth_required],
    )
    registry.add(
        "DELETE",
        "/{service_id}/routings/{route_id}",
        handler.delete_route,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/{service_id}/token",
        handler.generate_token,
        middlewares=[auth_required],
    )
