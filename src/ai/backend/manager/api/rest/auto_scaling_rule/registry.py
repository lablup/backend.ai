"""Auto-scaling rule sub-registry registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.server_status import READ_ALLOWED, server_status_required

from .handler import AutoScalingRuleHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps


def register_auto_scaling_rule_routes(deps: ModuleDeps) -> RouteRegistry:
    """Build the auto-scaling-rule sub-registry (child of admin)."""
    reg = RouteRegistry.create("auto-scaling-rules", deps.cors_options)
    handler = AutoScalingRuleHandler(processors=deps.processors)
    _middlewares = [server_status_required(READ_ALLOWED, deps.config_provider), auth_required]

    reg.add("POST", "", handler.create, middlewares=_middlewares)
    reg.add("GET", "/{rule_id}", handler.get, middlewares=_middlewares)
    reg.add("POST", "/search", handler.search, middlewares=_middlewares)
    reg.add("PATCH", "/{rule_id}", handler.update, middlewares=_middlewares)
    reg.add("POST", "/delete", handler.delete, middlewares=_middlewares)

    return reg
