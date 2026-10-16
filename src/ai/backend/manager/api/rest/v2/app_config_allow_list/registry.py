"""Route registry for REST v2 app config allow-list endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2AppConfigAllowListHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_app_config_allow_list_routes(
    handler: V2AppConfigAllowListHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 app config allow-list routes (superadmin only).

    Layout:
        POST   /                            register an allow-list entry
        POST   /search                      paginated search
        GET    /{app_config_allow_list_id}  get by id
        PATCH  /{app_config_allow_list_id}  update (rank) by id (deprecated)
        DELETE /{app_config_allow_list_id}  purge by id (deprecated)
    """
    registry = RouteRegistry.create("app-config-allow-list", route_deps.cors_options)

    registry.add("POST", "/", handler.admin_create, middlewares=[superadmin_required])
    registry.add("POST", "/search", handler.admin_search, middlewares=[superadmin_required])
    registry.add(
        "GET",
        "/{app_config_allow_list_id}",
        handler.admin_get,
        middlewares=[superadmin_required],
    )
    # Deprecated since NEXT_RELEASE_VERSION.
    registry.add(
        "PATCH",
        "/{app_config_allow_list_id}",
        handler.admin_update,
        middlewares=[superadmin_required],
    )
    registry.add(
        "DELETE",
        "/{app_config_allow_list_id}",
        handler.admin_purge,
        middlewares=[superadmin_required],
    )

    return registry


def register_v2_app_config_allow_lists_routes(
    handler: V2AppConfigAllowListHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register the REST v2 app config allow-list write routes.

    Layout:
        PATCH  /{app_config_allow_list_id}  update (rank) by id
        DELETE /{app_config_allow_list_id}  purge by id
        POST   /partial-bulk-update         update many by id
        POST   /partial-bulk-purge          purge many by id
    """
    registry = RouteRegistry.create("app-config-allow-lists", route_deps.cors_options)

    registry.add(
        "PATCH", "/{app_config_allow_list_id}", handler.update, middlewares=[auth_required]
    )
    registry.add(
        "DELETE", "/{app_config_allow_list_id}", handler.purge, middlewares=[auth_required]
    )
    registry.add(
        "POST", "/partial-bulk-update", handler.partial_bulk_update, middlewares=[auth_required]
    )
    registry.add(
        "POST", "/partial-bulk-purge", handler.partial_bulk_purge, middlewares=[auth_required]
    )

    return registry
