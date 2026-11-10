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

    Writes go through ``/atomic-bulk-upsert``: a fragment is addressed by ``(scope, config_name)`` rather
    than by id, so there is no separate create or update endpoint. The paginated scoped search
    is not exposed either — ``/by-names`` is the read a client needs before editing. Every
    route but ``/admin/search`` is open to any authenticated user and gated by RBAC at the
    processor (a user acts on their own user-scope, a domain admin on their domain's, a
    superadmin on any; public is superadmin-only). Only the system-wide ``/admin/search``
    skips RBAC, being superadmin-only at the middleware.

    Layout:
        POST   /partial-bulk-purge          purge many by id               (auth, RBAC)
        POST   /admin/search                system-wide paginated search   (superadmin)
        POST   /scoped/by-names             read one scope's by names      (auth, RBAC)
        POST   /scoped/atomic-bulk-upsert   upsert many at one scope       (auth, RBAC)
        POST   /my/by-names                 read own scope's by names      (auth)
        POST   /my/atomic-bulk-upsert       upsert many at own scope       (auth)
        GET    /{fragment_id}               get by id                      (auth, RBAC)
        DELETE /{fragment_id}               purge by id                    (auth, RBAC)
        POST   /bulk-delete                 purge many by id (deprecated)  (auth, RBAC)
        POST   /scoped/bulk-upsert          upsert many (deprecated)       (auth, RBAC)
        POST   /my/bulk-upsert              upsert many (deprecated)       (auth)
    """
    registry = RouteRegistry.create("app-config-fragments", route_deps.cors_options)

    registry.add(
        "POST", "/partial-bulk-purge", handler.partial_bulk_purge, middlewares=[auth_required]
    )
    registry.add("POST", "/admin/search", handler.admin_search, middlewares=[superadmin_required])
    registry.add(
        "POST", "/scoped/by-names", handler.scoped_fragments_by_names, middlewares=[auth_required]
    )
    registry.add(
        "POST",
        "/scoped/atomic-bulk-upsert",
        handler.scoped_atomic_bulk_upsert,
        middlewares=[auth_required],
    )
    registry.add("POST", "/my/by-names", handler.my_fragments_by_names, middlewares=[auth_required])
    registry.add(
        "POST", "/my/atomic-bulk-upsert", handler.my_atomic_bulk_upsert, middlewares=[auth_required]
    )
    registry.add("GET", "/{fragment_id}", handler.get, middlewares=[auth_required])
    registry.add("DELETE", "/{fragment_id}", handler.purge, middlewares=[auth_required])
    # Deprecated since NEXT_RELEASE_VERSION.
    registry.add("POST", "/bulk-delete", handler.bulk_purge, middlewares=[auth_required])
    registry.add(
        "POST", "/scoped/bulk-upsert", handler.scoped_bulk_upsert, middlewares=[auth_required]
    )
    registry.add("POST", "/my/bulk-upsert", handler.my_bulk_upsert, middlewares=[auth_required])

    return registry
