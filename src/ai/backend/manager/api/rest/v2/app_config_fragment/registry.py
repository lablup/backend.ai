"""Route registry for REST v2 app config fragment endpoints."""

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
    """Register all REST v2 app config fragment routes.

    Layout:
        POST   /                  create a fragment              (auth; write_access tier)
        POST   /search            admin paginated search         (superadmin)
        POST   /scoped-search     principal-visible search       (auth)
        GET    /{fragment_id}     get by id                      (superadmin)
        PATCH  /{fragment_id}     update config by id            (auth; write_access tier)
        DELETE /{fragment_id}     purge by id                    (auth; write_access tier)
    """
    registry = RouteRegistry.create("app-config-fragments", route_deps.cors_options)

    # Write routes are auth_required; the service authorizes each write against the target
    # layer's allow_list write_access tier (a superadmin passes any tier).
    registry.add("POST", "/", handler.create, middlewares=[auth_required])
    registry.add("POST", "/search", handler.admin_search, middlewares=[superadmin_required])
    registry.add("POST", "/scoped-search", handler.scoped_search, middlewares=[auth_required])
    registry.add("GET", "/{fragment_id}", handler.admin_get, middlewares=[superadmin_required])
    registry.add("PATCH", "/{fragment_id}", handler.update, middlewares=[auth_required])
    registry.add("DELETE", "/{fragment_id}", handler.purge, middlewares=[auth_required])

    return registry
