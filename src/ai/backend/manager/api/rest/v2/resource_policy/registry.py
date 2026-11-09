"""Route registration for v2 resource policy endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2ResourcePolicyHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps

# Matches a UUID only, so `PATCH /{name}` and `DELETE /{name}` (deprecated) still take every
# other name.
_POLICY_ID = (
    "{policy_id:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}}"
)


def register_v2_resource_policy_routes(
    handler: V2ResourcePolicyHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all v2 resource policy routes."""
    reg = RouteRegistry.create("resource-policies", route_deps.cors_options)

    # Keypair resource policy
    reg.add(
        "GET",
        "/keypair/{name}",
        handler.admin_get_keypair_resource_policy,
        middlewares=[superadmin_required],
    )
    reg.add(
        "POST",
        "/keypair/search",
        handler.admin_search_keypair_resource_policies,
        middlewares=[superadmin_required],
    )
    reg.add(
        "POST",
        "/keypair",
        handler.admin_create_keypair_resource_policy,
        middlewares=[superadmin_required],
    )
    reg.add(
        "PATCH",
        f"/keypair/{_POLICY_ID}",
        handler.update_keypair_resource_policy,
        middlewares=[auth_required],
    )
    reg.add(
        "DELETE",
        f"/keypair/{_POLICY_ID}",
        handler.purge_keypair_resource_policy,
        middlewares=[auth_required],
    )
    reg.add(
        "POST",
        "/keypair/partial-bulk-update",
        handler.partial_bulk_update_keypair_resource_policies,
        middlewares=[auth_required],
    )
    reg.add(
        "POST",
        "/keypair/partial-bulk-purge",
        handler.partial_bulk_purge_keypair_resource_policies,
        middlewares=[auth_required],
    )
    # Deprecated since NEXT_RELEASE_VERSION.
    reg.add(
        "PATCH",
        "/keypair/{name}",
        handler.admin_update_keypair_resource_policy,
        middlewares=[superadmin_required],
    )
    reg.add(
        "DELETE",
        "/keypair/{name}",
        handler.admin_delete_keypair_resource_policy,
        middlewares=[superadmin_required],
    )
    reg.add(
        "GET",
        "/keypair/my",
        handler.my_keypair_resource_policy,
        middlewares=[auth_required],
    )

    # User resource policy
    reg.add(
        "GET",
        "/user/{name}",
        handler.admin_get_user_resource_policy,
        middlewares=[superadmin_required],
    )
    reg.add(
        "POST",
        "/user/search",
        handler.admin_search_user_resource_policies,
        middlewares=[superadmin_required],
    )
    reg.add(
        "POST",
        "/user",
        handler.admin_create_user_resource_policy,
        middlewares=[superadmin_required],
    )
    reg.add(
        "PATCH",
        f"/user/{_POLICY_ID}",
        handler.update_user_resource_policy,
        middlewares=[auth_required],
    )
    reg.add(
        "DELETE",
        f"/user/{_POLICY_ID}",
        handler.purge_user_resource_policy,
        middlewares=[auth_required],
    )
    reg.add(
        "POST",
        "/user/partial-bulk-update",
        handler.partial_bulk_update_user_resource_policies,
        middlewares=[auth_required],
    )
    reg.add(
        "POST",
        "/user/partial-bulk-purge",
        handler.partial_bulk_purge_user_resource_policies,
        middlewares=[auth_required],
    )
    # Deprecated since NEXT_RELEASE_VERSION.
    reg.add(
        "PATCH",
        "/user/{name}",
        handler.admin_update_user_resource_policy,
        middlewares=[superadmin_required],
    )
    reg.add(
        "DELETE",
        "/user/{name}",
        handler.admin_delete_user_resource_policy,
        middlewares=[superadmin_required],
    )
    reg.add(
        "GET",
        "/user/my",
        handler.my_user_resource_policy,
        middlewares=[auth_required],
    )

    # Project resource policy
    reg.add(
        "GET",
        "/project/{name}",
        handler.admin_get_project_resource_policy,
        middlewares=[superadmin_required],
    )
    reg.add(
        "POST",
        "/project/search",
        handler.admin_search_project_resource_policies,
        middlewares=[superadmin_required],
    )
    reg.add(
        "POST",
        "/project",
        handler.admin_create_project_resource_policy,
        middlewares=[superadmin_required],
    )
    reg.add(
        "PATCH",
        f"/project/{_POLICY_ID}",
        handler.update_project_resource_policy,
        middlewares=[auth_required],
    )
    reg.add(
        "DELETE",
        f"/project/{_POLICY_ID}",
        handler.purge_project_resource_policy,
        middlewares=[auth_required],
    )
    reg.add(
        "POST",
        "/project/partial-bulk-update",
        handler.partial_bulk_update_project_resource_policies,
        middlewares=[auth_required],
    )
    reg.add(
        "POST",
        "/project/partial-bulk-purge",
        handler.partial_bulk_purge_project_resource_policies,
        middlewares=[auth_required],
    )
    # Deprecated since NEXT_RELEASE_VERSION.
    reg.add(
        "PATCH",
        "/project/{name}",
        handler.admin_update_project_resource_policy,
        middlewares=[superadmin_required],
    )
    reg.add(
        "DELETE",
        "/project/{name}",
        handler.admin_delete_project_resource_policy,
        middlewares=[superadmin_required],
    )
    reg.add(
        "GET",
        "/project/projects/{project_id}",
        handler.scoped_project_resource_policy,
        middlewares=[auth_required],
    )

    return reg
