"""Resource slot type module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import ResourceSlotHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_resource_slot_routes(
    handler: ResourceSlotHandler, route_deps: RouteDeps
) -> RouteRegistry:
    """Build the resource-slot-types sub-application."""
    reg = RouteRegistry.create("resource-slot-types", route_deps.cors_options)

    reg.add(
        "POST",
        "/search",
        handler.search_resource_slot_types,
        middlewares=[
            superadmin_required,
            route_deps.all_status_mw,
        ],
    )
    reg.add(
        "GET",
        "/{slot_name}",
        handler.get_resource_slot_type,
        middlewares=[
            superadmin_required,
            route_deps.all_status_mw,
        ],
    )
    return reg
