"""Route registration for v2 app-config fragment endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2AppConfigFragmentHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_app_config_fragment_routes(
    handler: V2AppConfigFragmentHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all v2 app-config fragment routes.

    - `POST /get` reads a single row via body (three-field natural key).
    - Scoped search mounts at `/{scope_type}/{scope_id}/search`.
    - Admin cross-scope search + bulk writes are admin-only.
    - `/my/bulk-create` and `/my/bulk-update` are self-service writes
      on the caller's `USER` row (no `/my/bulk-purge` — admin-only
      cleanup ).
    """
    reg = RouteRegistry.create("app-config-fragments", route_deps.cors_options)

    # Reads
    reg.add("POST", "/get", handler.get, middlewares=[auth_required])
    reg.add(
        "POST",
        "/{scope_type}/{scope_id}/search",
        handler.scoped_search,
        middlewares=[auth_required],
    )
    reg.add("POST", "/search", handler.admin_search, middlewares=[superadmin_required])
    # Admin bulk writes (bulk-only)
    reg.add("POST", "/bulk-create", handler.admin_bulk_create, middlewares=[superadmin_required])
    reg.add("POST", "/bulk-update", handler.admin_bulk_update, middlewares=[superadmin_required])
    reg.add("POST", "/bulk-purge", handler.admin_bulk_purge, middlewares=[superadmin_required])
    # Self-service bulk writes
    reg.add("POST", "/my/bulk-create", handler.my_bulk_create, middlewares=[auth_required])
    reg.add("POST", "/my/bulk-update", handler.my_bulk_update, middlewares=[auth_required])

    return reg
