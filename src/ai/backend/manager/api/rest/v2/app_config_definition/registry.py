"""Route registry for REST v2 app config definition endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2AppConfigDefinitionHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_app_config_definition_routes(
    handler: V2AppConfigDefinitionHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 app config definition routes (superadmin only).

    A config definition is an admin-only entity — every route is ``superadmin_required`` —
    so it carries no scoped search counterpart to ``/search``. A non-admin never queries
    definitions directly; they are read through the app config resolve path.

    Layout:
        POST   /                              register a config definition
        POST   /search                        paginated search
        GET    /{app_config_definition_id}    get by id
        DELETE /{app_config_definition_id}    purge by id
    """
    registry = RouteRegistry.create("app-config-definitions", route_deps.cors_options)

    registry.add("POST", "/", handler.admin_create, middlewares=[superadmin_required])
    registry.add("POST", "/search", handler.admin_search, middlewares=[superadmin_required])
    registry.add(
        "GET",
        "/{app_config_definition_id}",
        handler.admin_get,
        middlewares=[superadmin_required],
    )
    registry.add(
        "DELETE",
        "/{app_config_definition_id}",
        handler.admin_purge,
        middlewares=[superadmin_required],
    )

    return registry
