"""Route registry for REST v2 resource group endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2ResourceGroupHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps

# Matches a UUID only, so `PATCH /{name}` and `DELETE /{name}` (deprecated) still take every
# other name.
_RESOURCE_GROUP_ID = "{resource_group_id:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}}"


def register_v2_resource_group_routes(
    handler: V2ResourceGroupHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 resource group routes and return the sub-registry."""
    registry = RouteRegistry.create("resource-groups", route_deps.cors_options)

    registry.add(
        "POST",
        "/scoped/search",
        handler.scoped_search,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/search",
        handler.search,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "",
        handler.create,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/partial-bulk-update",
        handler.partial_bulk_update,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/partial-bulk-purge",
        handler.partial_bulk_purge,
        middlewares=[auth_required],
    )
    registry.add(
        "PATCH",
        f"/{_RESOURCE_GROUP_ID}",
        handler.update,
        middlewares=[auth_required],
    )
    registry.add(
        "DELETE",
        f"/{_RESOURCE_GROUP_ID}",
        handler.purge,
        middlewares=[auth_required],
    )
    registry.add(
        "GET",
        "/{name}",
        handler.get,
        middlewares=[superadmin_required],
    )
    # Deprecated since NEXT_RELEASE_VERSION.
    registry.add(
        "PATCH",
        "/{name}",
        handler.admin_update,
        middlewares=[superadmin_required],
    )
    # Deprecated since NEXT_RELEASE_VERSION.
    registry.add(
        "DELETE",
        "/{name}",
        handler.admin_delete,
        middlewares=[superadmin_required],
    )
    registry.add(
        "GET",
        "/{name}/resource-info",
        handler.get_resource_info,
        middlewares=[superadmin_required],
    )
    registry.add(
        "PATCH",
        "/{name}/fair-share-spec",
        handler.update_fair_share_spec,
        middlewares=[superadmin_required],
    )
    registry.add(
        "PATCH",
        "/{name}/config",
        handler.update_config,
        middlewares=[superadmin_required],
    )
    registry.add(
        "PUT",
        "/{name}/default-options",
        handler.admin_replace_default_deployment_options,
        middlewares=[superadmin_required],
    )
    registry.add(
        "PUT",
        "/{name}/default-session-options",
        handler.admin_replace_default_session_options,
        middlewares=[superadmin_required],
    )
    # Allow / Disallow routes
    registry.add(
        "GET",
        "/domains/{domain_name}/allowed",
        handler.get_allowed_rgs_for_domain,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/domains/{domain_name}/allowed",
        handler.update_allowed_rgs_for_domain,
        middlewares=[superadmin_required],
    )
    registry.add(
        "GET",
        "/projects/{project_id}/allowed",
        handler.get_allowed_rgs_for_project,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/projects/{project_id}/allowed",
        handler.update_allowed_rgs_for_project,
        middlewares=[superadmin_required],
    )
    registry.add(
        "GET",
        "/{name}/allowed-domains",
        handler.get_allowed_domains_for_rg,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/{name}/allowed-domains",
        handler.update_allowed_domains_for_rg,
        middlewares=[superadmin_required],
    )
    registry.add(
        "GET",
        "/{name}/allowed-projects",
        handler.get_allowed_projects_for_rg,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/{name}/allowed-projects",
        handler.update_allowed_projects_for_rg,
        middlewares=[superadmin_required],
    )

    return registry
