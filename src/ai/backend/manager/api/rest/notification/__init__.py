"""New-style notification module using RouteRegistry and constructor DI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import NotificationHandler

if TYPE_CHECKING:
    from ai.backend.manager.services.processors import Processors


def register_routes(
    registry: RouteRegistry,
    processors: Processors,
) -> None:
    """Register notification routes on the given RouteRegistry."""
    handler = NotificationHandler(processors=processors)

    # Channel routes
    registry.add(
        "POST",
        "/channels",
        handler.create_channel,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/channels/search",
        handler.search_channels,
        middlewares=[superadmin_required],
    )
    registry.add(
        "GET",
        "/channels/{channel_id}",
        handler.get_channel,
        middlewares=[superadmin_required],
    )
    registry.add(
        "PATCH",
        "/channels/{channel_id}",
        handler.update_channel,
        middlewares=[superadmin_required],
    )
    registry.add(
        "DELETE",
        "/channels/{channel_id}",
        handler.delete_channel,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/channels/{channel_id}/validate",
        handler.validate_channel,
        middlewares=[superadmin_required],
    )

    # Rule type routes
    registry.add(
        "GET",
        "/rule-types",
        handler.list_rule_types,
        middlewares=[superadmin_required],
    )
    registry.add(
        "GET",
        "/rule-types/{rule_type}/schema",
        handler.get_rule_type_schema,
        middlewares=[superadmin_required],
    )

    # Rule routes
    registry.add(
        "POST",
        "/rules",
        handler.create_rule,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/rules/search",
        handler.search_rules,
        middlewares=[superadmin_required],
    )
    registry.add(
        "GET",
        "/rules/{rule_id}",
        handler.get_rule,
        middlewares=[superadmin_required],
    )
    registry.add(
        "PATCH",
        "/rules/{rule_id}",
        handler.update_rule,
        middlewares=[superadmin_required],
    )
    registry.add(
        "DELETE",
        "/rules/{rule_id}",
        handler.delete_rule,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/rules/{rule_id}/validate",
        handler.validate_rule,
        middlewares=[superadmin_required],
    )
