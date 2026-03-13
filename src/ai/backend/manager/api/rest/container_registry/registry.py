"""Container registry module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import ContainerRegistryHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_container_registry_routes(
    handler: ContainerRegistryHandler, route_deps: RouteDeps
) -> RouteRegistry:
    """Build the container registry sub-application."""
    reg = RouteRegistry.create("container-registries", route_deps.cors_options)

    reg.add(
        "POST",
        "/",
        handler.create,
        middlewares=[
            route_deps.read_status_mw,
            superadmin_required,
        ],
    )
    reg.add(
        "GET",
        "/",
        handler.list_all,
        middlewares=[
            route_deps.read_status_mw,
            superadmin_required,
        ],
    )
    reg.add(
        "GET",
        "/load",
        handler.load,
        middlewares=[
            route_deps.read_status_mw,
            superadmin_required,
        ],
    )
    reg.add(
        "PATCH",
        "/{registry_id}",
        handler.patch,
        middlewares=[
            route_deps.read_status_mw,
            superadmin_required,
        ],
    )
    reg.add(
        "DELETE",
        "/{registry_id}",
        handler.delete,
        middlewares=[
            route_deps.read_status_mw,
            superadmin_required,
        ],
    )
    reg.add(
        "POST",
        "/rescan",
        handler.rescan_images,
        middlewares=[
            route_deps.read_status_mw,
            superadmin_required,
        ],
    )
    reg.add(
        "POST",
        "/clear",
        handler.clear_images,
        middlewares=[
            route_deps.read_status_mw,
            superadmin_required,
        ],
    )
    reg.add(
        "POST",
        "/webhook/harbor",
        handler.harbor_webhook,
        middlewares=[route_deps.all_status_mw],
    )
    return reg
