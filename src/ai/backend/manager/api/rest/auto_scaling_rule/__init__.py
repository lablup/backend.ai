"""New-style auto-scaling rule module using RouteRegistry and constructor DI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.manager import READ_ALLOWED, server_status_required
from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import AutoScalingRuleHandler

if TYPE_CHECKING:
    from ai.backend.manager.services.processors import Processors


def register_routes(
    registry: RouteRegistry,
    processors: Processors,
) -> None:
    """Register auto-scaling rule routes on the given RouteRegistry."""
    handler = AutoScalingRuleHandler(processors=processors)
    _middlewares = [server_status_required(READ_ALLOWED), auth_required]

    registry.add("POST", "", handler.create, middlewares=_middlewares)
    registry.add("GET", "/{rule_id}", handler.get, middlewares=_middlewares)
    registry.add("POST", "/search", handler.search, middlewares=_middlewares)
    registry.add("PATCH", "/{rule_id}", handler.update, middlewares=_middlewares)
    registry.add("POST", "/delete", handler.delete, middlewares=_middlewares)
