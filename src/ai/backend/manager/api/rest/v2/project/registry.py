"""Route registration for v2 project endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2ProjectHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_project_routes(
    handler: V2ProjectHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all v2 project routes."""
    reg = RouteRegistry.create("projects", route_deps.cors_options)
    reg.add("GET", "/{project_id}", handler.get, middlewares=[auth_required])
    reg.add("POST", "/search", handler.admin_search, middlewares=[superadmin_required])
    reg.add("POST", "/my/search", handler.my_search, middlewares=[auth_required])
    reg.add("POST", "/scoped/search", handler.scoped_search, middlewares=[auth_required])
    reg.add("POST", "", handler.admin_create, middlewares=[superadmin_required])
    reg.add("PATCH", "/{project_id}", handler.update, middlewares=[auth_required])
    reg.add("POST", "/{project_id}/delete", handler.delete, middlewares=[auth_required])
    reg.add("POST", "/{project_id}/restore", handler.restore, middlewares=[auth_required])
    reg.add(
        "POST", "/partial-bulk-update", handler.partial_bulk_update, middlewares=[auth_required]
    )
    reg.add(
        "POST", "/partial-bulk-delete", handler.partial_bulk_delete, middlewares=[auth_required]
    )
    reg.add(
        "POST", "/partial-bulk-restore", handler.partial_bulk_restore, middlewares=[auth_required]
    )
    reg.add("POST", "/purge", handler.admin_purge, middlewares=[superadmin_required])
    reg.add(
        "POST",
        "/{project_id}/users/assign",
        handler.assign_users,
        middlewares=[auth_required],
    )
    reg.add(
        "POST",
        "/{project_id}/users/unassign",
        handler.unassign_users,
        middlewares=[auth_required],
    )
    # Deprecated since NEXT_RELEASE_VERSION.
    reg.add("POST", "/delete", handler.admin_delete, middlewares=[superadmin_required])
    reg.add("POST", "/restore", handler.admin_restore, middlewares=[superadmin_required])
    return reg
