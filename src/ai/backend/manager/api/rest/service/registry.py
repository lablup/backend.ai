"""Service (model serving) module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps


def register_service_routes(deps: ModuleDeps) -> RouteRegistry:
    """Build the service (model serving) sub-application."""
    from ai.backend.manager.api.service import (
        PrivateContext as ServicePrivateContext,
    )
    from ai.backend.manager.api.service import (
        init as service_init,
    )
    from ai.backend.manager.api.service import (
        shutdown as service_shutdown,
    )

    from .handler import ServiceHandler

    reg = RouteRegistry.create("services", deps.cors_options)
    ctx = ServicePrivateContext()

    # Store ctx on app dict for backward compatibility (lifecycle functions
    # read from app["services.context"]).
    reg.app["services.context"] = ctx

    # Wire lifecycle hooks
    reg.app.on_startup.append(service_init)
    reg.app.on_shutdown.append(service_shutdown)
    handler = ServiceHandler(
        processors=deps.processors,
    )

    # Service list & create (root)
    reg.add("GET", "", handler.list_serve, middlewares=[auth_required])
    reg.add("POST", "", handler.create, middlewares=[auth_required])

    # Search & utilities
    reg.add("POST", "/_/search", handler.search_services, middlewares=[auth_required])
    reg.add("POST", "/_/try", handler.try_start, middlewares=[auth_required])
    reg.add(
        "GET",
        "/_/runtimes",
        handler.list_supported_runtimes,
        middlewares=[auth_required],
    )

    # Per-service endpoints
    reg.add("GET", "/{service_id}", handler.get_info, middlewares=[auth_required])
    reg.add("DELETE", "/{service_id}", handler.delete, middlewares=[auth_required])
    reg.add(
        "GET",
        "/{service_id}/errors",
        handler.list_errors,
        middlewares=[auth_required],
    )
    reg.add(
        "POST",
        "/{service_id}/errors/clear",
        handler.clear_error,
        middlewares=[auth_required],
    )
    reg.add(
        "POST",
        "/{service_id}/scale",
        handler.scale,
        middlewares=[auth_required],
    )
    reg.add(
        "POST",
        "/{service_id}/sync",
        handler.sync,
        middlewares=[auth_required],
    )
    reg.add(
        "PUT",
        "/{service_id}/routings/{route_id}",
        handler.update_route,
        middlewares=[auth_required],
    )
    reg.add(
        "DELETE",
        "/{service_id}/routings/{route_id}",
        handler.delete_route,
        middlewares=[auth_required],
    )
    reg.add(
        "POST",
        "/{service_id}/token",
        handler.generate_token,
        middlewares=[auth_required],
    )
    return reg
