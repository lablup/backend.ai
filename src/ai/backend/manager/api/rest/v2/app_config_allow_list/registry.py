"""Route registry for REST v2 app config allow-list endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2AppConfigAllowListHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_app_config_allow_list_routes(
    handler: V2AppConfigAllowListHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 app config allow-list routes (superadmin only).

    The allow-list is an admin-only entity — every route is ``superadmin_required`` — so
    it carries no scoped search counterpart to ``/search``. A non-admin never queries the
    allow-list directly; it is read through the app config resolve path.

    Layout:
        POST   /                            register an allow-list entry
        POST   /search                      paginated search
        GET    /{app_config_allow_list_id}  get by id
        PATCH  /{app_config_allow_list_id}  update (rank) by id
        DELETE /{app_config_allow_list_id}  purge by id
    """
    registry = RouteRegistry.create("app-config-allow-lists", route_deps.cors_options)

    registry.add("POST", "/", handler.admin_create, middlewares=[superadmin_required])
    registry.add("POST", "/search", handler.admin_search, middlewares=[superadmin_required])
    registry.add(
        "GET",
        "/{app_config_allow_list_id}",
        handler.admin_get,
        middlewares=[superadmin_required],
    )
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
