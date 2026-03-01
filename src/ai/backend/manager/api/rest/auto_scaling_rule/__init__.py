from __future__ import annotations

from typing import TYPE_CHECKING

from .registry import register_auto_scaling_rule_routes

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.routing import RouteRegistry
    from ai.backend.manager.services.processors import Processors

__all__ = ["register_auto_scaling_rule_routes"]


def register_routes(registry: RouteRegistry, processors: Processors) -> None:
    """Backward-compatible shim — delegates to the old inline logic.

    The canonical entry-point is :func:`register_auto_scaling_rule_routes`; this wrapper
    exists only so that ``server.py`` keeps working until it is migrated to
    the new ``ModuleDeps`` convention.
    """
    from ai.backend.manager.api.manager import READ_ALLOWED, server_status_required
    from ai.backend.manager.api.rest.middleware.auth import auth_required

    from .handler import AutoScalingRuleHandler

    handler = AutoScalingRuleHandler(processors=processors)
    _middlewares = [server_status_required(READ_ALLOWED), auth_required]

    registry.add("POST", "", handler.create, middlewares=_middlewares)
    registry.add("GET", "/{rule_id}", handler.get, middlewares=_middlewares)
    registry.add("POST", "/search", handler.search, middlewares=_middlewares)
    registry.add("PATCH", "/{rule_id}", handler.update, middlewares=_middlewares)
    registry.add("POST", "/delete", handler.delete, middlewares=_middlewares)
