"""Route registry for REST v2 retention policy endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2RetentionPolicyHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_retention_policy_routes(
    handler: V2RetentionPolicyHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 retention policy routes.

    Layout:
        POST   /                        create a retention policy
        POST   /search                  paginated search
        GET    /{policy_id}             get by id
        PATCH  /{policy_id}             update (period / enabled) by id
        DELETE /{policy_id}             purge (permanently remove) by id
        POST   /partial-bulk-update     update several
        POST   /partial-bulk-purge      purge several
        POST   /{policy_id}/purge       purge by id (deprecated)
    """
    registry = RouteRegistry.create("retention-policies", route_deps.cors_options)

    registry.add("POST", "", handler.admin_create, middlewares=[superadmin_required])
    registry.add("POST", "/search", handler.admin_search, middlewares=[superadmin_required])
    registry.add("GET", "/{policy_id}", handler.admin_get, middlewares=[superadmin_required])
    registry.add("PATCH", "/{policy_id}", handler.update, middlewares=[auth_required])
    registry.add("DELETE", "/{policy_id}", handler.purge, middlewares=[auth_required])
    registry.add(
        "POST", "/partial-bulk-update", handler.partial_bulk_update, middlewares=[auth_required]
    )
    registry.add(
        "POST", "/partial-bulk-purge", handler.partial_bulk_purge, middlewares=[auth_required]
    )
    # Deprecated since NEXT_RELEASE_VERSION.
    registry.add(
        "POST", "/{policy_id}/purge", handler.admin_purge, middlewares=[superadmin_required]
    )

    return registry
