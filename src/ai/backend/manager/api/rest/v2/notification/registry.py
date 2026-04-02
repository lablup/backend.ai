"""Route registration for v2 notification endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2NotificationHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_notification_routes(
    handler: V2NotificationHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all v2 notification routes."""
    reg = RouteRegistry.create("notifications", route_deps.cors_options)

    # Channel endpoints
    reg.add("POST", "/channels", handler.create_channel, middlewares=[superadmin_required])
    reg.add("GET", "/channels/{channel_id}", handler.get_channel, middlewares=[superadmin_required])
    reg.add(
        "PATCH", "/channels/{channel_id}", handler.update_channel, middlewares=[superadmin_required]
    )
    reg.add("POST", "/channels/delete", handler.delete_channel, middlewares=[superadmin_required])
    reg.add("POST", "/channels/search", handler.search_channels, middlewares=[superadmin_required])
    reg.add(
        "POST", "/channels/validate", handler.validate_channel, middlewares=[superadmin_required]
    )

    # Rule endpoints
    reg.add("POST", "/rules", handler.create_rule, middlewares=[superadmin_required])
    reg.add("GET", "/rules/{rule_id}", handler.get_rule, middlewares=[superadmin_required])
    reg.add("PATCH", "/rules/{rule_id}", handler.update_rule, middlewares=[superadmin_required])
    reg.add("POST", "/rules/delete", handler.delete_rule, middlewares=[superadmin_required])
    reg.add("POST", "/rules/search", handler.search_rules, middlewares=[superadmin_required])
    reg.add("POST", "/rules/validate", handler.validate_rule, middlewares=[superadmin_required])

    return reg
