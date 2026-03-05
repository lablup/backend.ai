"""Session template module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import SessionTemplateHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_session_template_routes(
    handler: SessionTemplateHandler, route_deps: RouteDeps
) -> RouteRegistry:
    """Build the session template sub-application."""
    reg = RouteRegistry.create("session", route_deps.cors_options)
    _middlewares = [route_deps.read_status_mw, auth_required]

    reg.add("POST", "", handler.create, middlewares=_middlewares)
    reg.add("GET", "", handler.list_templates, middlewares=_middlewares)
    reg.add("GET", "/{template_id}", handler.get, middlewares=_middlewares)
    reg.add("PUT", "/{template_id}", handler.update, middlewares=_middlewares)
    reg.add("DELETE", "/{template_id}", handler.delete, middlewares=_middlewares)
    return reg
