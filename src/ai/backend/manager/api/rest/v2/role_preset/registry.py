"""Route registry for REST v2 role preset endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2RolePresetHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_role_preset_routes(
    handler: V2RolePresetHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all v2 role preset routes.

    Delete is a soft-delete, Restore inverts it, and Purge is the hard delete.
    """
    registry = RouteRegistry.create("role-presets", route_deps.cors_options)

    registry.add("POST", "", handler.create, middlewares=[superadmin_required])
    registry.add("POST", "/search", handler.search, middlewares=[superadmin_required])
    registry.add(
        "POST", "/partial-bulk-update", handler.partial_bulk_update, middlewares=[auth_required]
    )
    registry.add(
        "POST", "/partial-bulk-delete", handler.partial_bulk_delete, middlewares=[auth_required]
    )
    registry.add(
        "POST", "/partial-bulk-restore", handler.partial_bulk_restore, middlewares=[auth_required]
    )
    registry.add(
        "POST", "/partial-bulk-purge", handler.partial_bulk_purge, middlewares=[auth_required]
    )
    registry.add(
        "POST", "/permissions/remove", handler.remove_permissions, middlewares=[superadmin_required]
    )
    registry.add("GET", "/{role_preset_id}", handler.get, middlewares=[superadmin_required])
    registry.add("PATCH", "/{role_preset_id}", handler.update, middlewares=[auth_required])
    registry.add("POST", "/{role_preset_id}/delete", handler.delete, middlewares=[auth_required])
    registry.add("POST", "/{role_preset_id}/restore", handler.restore, middlewares=[auth_required])
    registry.add("DELETE", "/{role_preset_id}", handler.purge, middlewares=[auth_required])
    registry.add(
        "POST",
        "/{role_preset_id}/permissions/search",
        handler.search_permissions,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/{role_preset_id}/permissions/add",
        handler.add_permissions,
        middlewares=[superadmin_required],
    )
    # Deprecated since NEXT_RELEASE_VERSION.
    registry.add("POST", "/bulk-delete", handler.bulk_delete, middlewares=[superadmin_required])
    registry.add("POST", "/bulk-restore", handler.bulk_restore, middlewares=[superadmin_required])
    registry.add("POST", "/bulk-purge", handler.bulk_purge, middlewares=[superadmin_required])

    return registry
