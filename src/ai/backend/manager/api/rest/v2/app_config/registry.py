"""Route registry for REST v2 merged app config endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2AppConfigHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_app_config_routes(
    handler: V2AppConfigHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 merged app config routes.

    Layout:
        POST /my/get       get the acting user's merged configs   (auth)
        POST /public/get   get the merged public configs          (anonymous)
    """
    registry = RouteRegistry.create("app-config", route_deps.cors_options)

    registry.add("POST", "/my/get", handler.my_get_app_configs, middlewares=[auth_required])
    # Anonymous (pre-login) public read: no auth middleware.
    registry.add("POST", "/public/get", handler.public_get_app_configs)

    return registry
