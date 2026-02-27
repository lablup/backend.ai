"""New-style cluster template module using RouteRegistry and constructor DI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.manager import READ_ALLOWED, server_status_required
from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import ClusterTemplateHandler

if TYPE_CHECKING:
    from ai.backend.manager.services.processors import Processors


def register_routes(
    registry: RouteRegistry,
    processors: Processors,
) -> None:
    """Register cluster template routes on the given RouteRegistry."""
    handler = ClusterTemplateHandler(processors=processors)
    _middlewares = [server_status_required(READ_ALLOWED), auth_required]

    registry.add("POST", "/template/cluster", handler.create, middlewares=_middlewares)
    registry.add("GET", "/template/cluster", handler.list_templates, middlewares=_middlewares)
    registry.add("GET", "/template/cluster/{template_id}", handler.get, middlewares=_middlewares)
    registry.add("PUT", "/template/cluster/{template_id}", handler.update, middlewares=_middlewares)
    registry.add(
        "DELETE", "/template/cluster/{template_id}", handler.delete, middlewares=_middlewares
    )
