"""Route registration for v2 app configuration endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2AppConfigHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_app_config_routes(
    handler: V2AppConfigHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all v2 app configuration routes."""
    reg = RouteRegistry.create("app-configs", route_deps.cors_options)

    # Domain config endpoints
    reg.add(
        "GET",
        "/domains/{domain_name}",
        handler.get_domain_config,
        middlewares=[superadmin_required],
    )
    reg.add(
        "PUT",
        "/domains/{domain_name}",
        handler.upsert_domain_config,
        middlewares=[superadmin_required],
    )
    reg.add(
        "DELETE",
        "/domains/{domain_name}",
        handler.delete_domain_config,
        middlewares=[superadmin_required],
    )

    # User config endpoints
    reg.add("GET", "/users/{user_id}", handler.get_user_config, middlewares=[superadmin_required])
    reg.add(
        "PUT", "/users/{user_id}", handler.upsert_user_config, middlewares=[superadmin_required]
    )
    reg.add(
        "DELETE", "/users/{user_id}", handler.delete_user_config, middlewares=[superadmin_required]
    )

    # Merged config endpoint
    reg.add(
        "GET",
        "/users/{user_id}/merged",
        handler.get_merged_config,
        middlewares=[superadmin_required],
    )

    return reg
