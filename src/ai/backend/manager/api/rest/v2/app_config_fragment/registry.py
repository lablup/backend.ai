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

    Every route but ``/admin/search`` is open to any authenticated user and gated by RBAC at
    the processor (a user acts on their own user-scope, a domain admin on their domain's, a
    superadmin on any; public is superadmin-only). ``/scoped/search`` is no exception: it
    runs the same scope validator as a write at that scope. Only the system-wide
    ``/admin/search`` skips RBAC, being superadmin-only at the middleware.

    Layout:
        POST   /                  create a fragment              (auth, RBAC)
        POST   /bulk-update       update many by id              (auth, RBAC)
        POST   /bulk-delete       purge many by id               (auth, RBAC)
        POST   /admin/search      system-wide paginated search   (superadmin)
        POST   /scoped/search     search one scope's fragments   (auth, RBAC)
        GET    /{fragment_id}     get by id                      (auth, RBAC)
        PATCH  /{fragment_id}     update config by id            (auth, RBAC)
        DELETE /{fragment_id}     purge by id                    (auth, RBAC)
    """
    registry = RouteRegistry.create("app-config-fragments", route_deps.cors_options)

    registry.add("POST", "/", handler.create, middlewares=[auth_required])
    registry.add("POST", "/bulk-update", handler.bulk_update, middlewares=[auth_required])
    registry.add("POST", "/bulk-delete", handler.bulk_purge, middlewares=[auth_required])
    registry.add("POST", "/admin/search", handler.admin_search, middlewares=[superadmin_required])
    registry.add("POST", "/scoped/search", handler.scoped_search, middlewares=[auth_required])
    registry.add("GET", "/{fragment_id}", handler.get, middlewares=[auth_required])
    registry.add("PATCH", "/{fragment_id}", handler.update, middlewares=[auth_required])
    registry.add("DELETE", "/{fragment_id}", handler.purge, middlewares=[auth_required])

    return registry
