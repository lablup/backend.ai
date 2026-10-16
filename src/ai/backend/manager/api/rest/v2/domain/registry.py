"""Route registration for v2 domain endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2DomainHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps

# Matches a UUID only, so `PATCH /{domain_name}` (deprecated) still takes every other name.
_DOMAIN_ID = (
    "{domain_id:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}}"
)


def register_v2_domain_routes(
    handler: V2DomainHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all v2 domain routes."""
    reg = RouteRegistry.create("domains", route_deps.cors_options)
    reg.add("GET", "/{domain_name}", handler.get, middlewares=[auth_required])
    reg.add("POST", "/search", handler.admin_search, middlewares=[superadmin_required])
    reg.add("POST", "/scoped/search", handler.scoped_search, middlewares=[auth_required])
    reg.add("POST", "", handler.admin_create, middlewares=[superadmin_required])
    reg.add("PATCH", f"/{_DOMAIN_ID}", handler.update, middlewares=[auth_required])
    reg.add("POST", "/{domain_id}/delete", handler.delete, middlewares=[auth_required])
    reg.add("POST", "/{domain_id}/restore", handler.restore, middlewares=[auth_required])
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
    # Deprecated since NEXT_RELEASE_VERSION.
    reg.add("PATCH", "/{domain_name}", handler.admin_update, middlewares=[superadmin_required])
    reg.add("POST", "/delete", handler.admin_delete, middlewares=[superadmin_required])
    reg.add("POST", "/restore", handler.admin_restore, middlewares=[superadmin_required])
    return reg
