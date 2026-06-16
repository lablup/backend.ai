"""Route registration for v2 AppConfig merged-view endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2AppConfigHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_app_config_routes(
    handler: V2AppConfigHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all v2 `/v2/app-configs/*` routes.

    Read-only surface — writes go through `/v2/app-config-fragments/...`
    (§4). Search has two variants: scoped (non-admin, scope in the body)
    and admin (superadmin). There is no `/my/...` route — self-service is
    a USER-scoped search.
    """
    reg = RouteRegistry.create("app-configs", route_deps.cors_options)

    # Scoped (non-admin) — scope required in the request body
    reg.add("POST", "/scoped/search", handler.scoped_search, middlewares=[auth_required])
    # Admin
    reg.add("POST", "/search", handler.admin_search, middlewares=[superadmin_required])
    reg.add("GET", "/{user_id}/{name}", handler.admin_get, middlewares=[superadmin_required])

    return reg
