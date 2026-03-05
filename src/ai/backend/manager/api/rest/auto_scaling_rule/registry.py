"""Auto-scaling rule sub-registry registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import AutoScalingRuleHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_auto_scaling_rule_routes(
    handler: AutoScalingRuleHandler, route_deps: RouteDeps
) -> RouteRegistry:
    """Build the auto-scaling-rule sub-registry (child of admin)."""
    reg = RouteRegistry.create("auto-scaling-rules", route_deps.cors_options)
    _middlewares = [route_deps.read_status_mw, auth_required]

    reg.add("POST", "", handler.create, middlewares=_middlewares)
    reg.add("GET", "/{rule_id}", handler.get, middlewares=_middlewares)
    reg.add("POST", "/search", handler.search, middlewares=_middlewares)
    reg.add("PATCH", "/{rule_id}", handler.update, middlewares=_middlewares)
    reg.add("POST", "/delete", handler.delete, middlewares=_middlewares)

    return reg
