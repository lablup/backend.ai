"""Route registry for REST v2 RBAC endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2RBACHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps

_ROLE_ID = "{role_id:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}}"


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
        f"/roles/{_ROLE_ID}",
        handler.update_role,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        f"/roles/{_ROLE_ID}/delete",
        handler.delete_role,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        f"/roles/{_ROLE_ID}/restore",
        handler.restore_role,
        middlewares=[auth_required],
    )
    registry.add(
        "DELETE",
        f"/roles/{_ROLE_ID}",
        handler.purge_role,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/roles/partial-bulk-update",
        handler.partial_bulk_update_roles,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/roles/partial-bulk-delete",
        handler.partial_bulk_delete_roles,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/roles/partial-bulk-restore",
        handler.partial_bulk_restore_roles,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/roles/partial-bulk-purge",
        handler.partial_bulk_purge_roles,
        middlewares=[auth_required],
    )
    # Deprecated since NEXT_RELEASE_VERSION.
    registry.add(
        "POST",
        "/roles/delete",
        handler.admin_delete_role,
        middlewares=[superadmin_required],
    )
    # Deprecated since NEXT_RELEASE_VERSION.
    registry.add(
        "POST",
        "/roles/purge",
        handler.admin_purge_role,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/roles/my/search",
        handler.my_search_roles,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/roles/projects/{project_id}/search",
        handler.project_search_roles,
        middlewares=[auth_required],
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
    registry.add(
        "POST",
        "/permissions/bulk-add",
        handler.bulk_add_role_permissions,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/permissions/bulk-remove",
        handler.bulk_remove_role_permissions,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/permissions/replace",
        handler.replace_role_permissions,
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
        "/assignments/my/search",
        handler.my_search_assignments,
        middlewares=[auth_required],
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

    # Permission Matrix
    registry.add(
        "GET",
        "/permission-matrix",
        handler.get_permission_matrix,
        middlewares=[auth_required],
    )

    return registry
