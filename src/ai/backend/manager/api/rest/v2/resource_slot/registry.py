"""Route registry for REST v2 resource slot endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2ResourceSlotHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps

# Matches a UUID only, so `DELETE /slot-types/{slot_name}` (deprecated) still takes every
# other name.
_SLOT_TYPE_ID = (
    "{slot_type_id:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}}"
)


def register_v2_resource_slot_routes(
    handler: V2ResourceSlotHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 resource slot routes and return the sub-registry."""
    registry = RouteRegistry.create("resource-slots", route_deps.cors_options)

    registry.add(
        "POST",
        "/slot-types/search",
        handler.search_slot_types,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/slot-types",
        handler.admin_create_slot_type,
        middlewares=[superadmin_required],
    )
    registry.add(
        "PATCH",
        "/slot-types/{slot_name}",
        handler.admin_update_slot_type,
        middlewares=[superadmin_required],
    )
    registry.add(
        "DELETE",
        f"/slot-types/{_SLOT_TYPE_ID}",
        handler.purge_slot_type,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/slot-types/partial-bulk-purge",
        handler.partial_bulk_purge_slot_types,
        middlewares=[auth_required],
    )
    # Deprecated since NEXT_RELEASE_VERSION.
    registry.add(
        "DELETE",
        "/slot-types/{slot_name}",
        handler.admin_purge_slot_type,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/agent-resources/scoped/search",
        handler.scoped_search_agent_resources,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/agent-resources/search",
        handler.search_agent_resources,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/allocations/search",
        handler.search_allocations,
        middlewares=[superadmin_required],
    )

    return registry
