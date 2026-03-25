"""Route registry for REST v2 RBAC endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2RBACHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_rbac_routes(
    handler: V2RBACHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 RBAC routes and return the sub-registry."""
    registry = RouteRegistry.create("rbac", route_deps.cors_options)

    # Roles
    registry.add(
        "POST",
        "/roles",
        handler.create_role,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/roles/search",
        handler.search_roles,
        middlewares=[superadmin_required],
    )
    registry.add(
        "GET",
        "/roles/{role_id}",
        handler.get_role,
        middlewares=[superadmin_required],
    )
    registry.add(
        "PATCH",
        "/roles/{role_id}",
        handler.update_role,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/roles/delete",
        handler.delete_role,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/roles/purge",
        handler.purge_role,
        middlewares=[superadmin_required],
    )

    # Permissions
    registry.add(
        "POST",
        "/permissions",
        handler.create_permission,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/permissions/search",
        handler.search_permissions,
        middlewares=[superadmin_required],
    )
    registry.add(
        "PATCH",
        "/permissions",
        handler.update_permission,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/permissions/delete",
        handler.delete_permission,
        middlewares=[superadmin_required],
    )

    # Assignments
    registry.add(
        "POST",
        "/assignments",
        handler.assign_role,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/assignments/revoke",
        handler.revoke_role,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/assignments/search",
        handler.search_assignments,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/assignments/bulk-assign",
        handler.bulk_assign_role,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/assignments/bulk-revoke",
        handler.bulk_revoke_role,
        middlewares=[superadmin_required],
    )

    # Entities
    registry.add(
        "POST",
        "/entities/search",
        handler.search_entities,
        middlewares=[superadmin_required],
    )

    return registry
