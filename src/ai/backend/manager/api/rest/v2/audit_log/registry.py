"""Route registry for REST v2 audit log endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2AuditLogHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_audit_log_routes(
    handler: V2AuditLogHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 audit log routes and return the sub-registry."""
    registry = RouteRegistry.create("audit-logs", route_deps.cors_options)

    registry.add(
        "POST",
        "/search",
        handler.admin_search_audit_logs,
        middlewares=[superadmin_required],
    )

    return registry
