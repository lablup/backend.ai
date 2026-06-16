"""Route registration for v2 app-config policy endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2AppConfigPolicyHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_app_config_policy_routes(
    handler: V2AppConfigPolicyHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all v2 app-config policy routes.

    `GET /{policy_id}` is available to any authenticated user. The
    system-wide search and the bulk writes are admin-only —
    `/search`, `/bulk-create`, `/bulk-update`, `/bulk-purge`.
    """
    reg = RouteRegistry.create("app-config-policies", route_deps.cors_options)

    # Reads
    reg.add("GET", "/{policy_id}", handler.get, middlewares=[auth_required])
    # Admin reads / bulk writes
    reg.add("POST", "/search", handler.admin_search, middlewares=[superadmin_required])
    reg.add("POST", "/bulk-create", handler.admin_bulk_create, middlewares=[superadmin_required])
    reg.add("POST", "/bulk-update", handler.admin_bulk_update, middlewares=[superadmin_required])
    reg.add("POST", "/bulk-purge", handler.admin_bulk_purge, middlewares=[superadmin_required])

    return reg
