"""Notification module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import NotificationHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_notification_routes(
    handler: NotificationHandler, route_deps: RouteDeps
) -> RouteRegistry:
    """Build the notification sub-application."""

    reg = RouteRegistry.create("notifications", route_deps.cors_options)

    # Channel routes
    reg.add(
        "POST",
        "/channels",
        handler.create_channel,
        middlewares=[superadmin_required],
    )
    reg.add(
        "POST",
        "/channels/search",
        handler.search_channels,
        middlewares=[superadmin_required],
    )
    reg.add(
        "GET",
        "/channels/{channel_id}",
        handler.get_channel,
        middlewares=[superadmin_required],
    )
    reg.add(
        "PATCH",
        "/channels/{channel_id}",
        handler.update_channel,
        middlewares=[superadmin_required],
    )
    reg.add(
        "DELETE",
        "/channels/{channel_id}",
        handler.delete_channel,
        middlewares=[superadmin_required],
    )
    reg.add(
        "POST",
        "/channels/{channel_id}/validate",
        handler.validate_channel,
        middlewares=[superadmin_required],
    )

    # Rule type routes
    reg.add(
        "GET",
        "/rule-types",
        handler.list_rule_types,
        middlewares=[superadmin_required],
    )
    reg.add(
        "GET",
        "/rule-types/{rule_type}/schema",
        handler.get_rule_type_schema,
        middlewares=[superadmin_required],
    )

    # Rule routes
    reg.add(
        "POST",
        "/rules",
        handler.create_rule,
        middlewares=[superadmin_required],
    )
    reg.add(
        "POST",
        "/rules/search",
        handler.search_rules,
        middlewares=[superadmin_required],
    )
    reg.add(
        "GET",
        "/rules/{rule_id}",
        handler.get_rule,
        middlewares=[superadmin_required],
    )
    reg.add(
        "PATCH",
        "/rules/{rule_id}",
        handler.update_rule,
        middlewares=[superadmin_required],
    )
    reg.add(
        "DELETE",
        "/rules/{rule_id}",
        handler.delete_rule,
        middlewares=[superadmin_required],
    )
    reg.add(
        "POST",
        "/rules/{rule_id}/validate",
        handler.validate_rule,
        middlewares=[superadmin_required],
    )
    return reg
