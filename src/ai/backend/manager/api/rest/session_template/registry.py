"""Session template module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.server_status import READ_ALLOWED, server_status_required

from .handler import SessionTemplateHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps


def register_session_template_routes(deps: ModuleDeps) -> RouteRegistry:
    """Build the session template sub-application."""
    reg = RouteRegistry.create("session", deps.cors_options)
    handler = SessionTemplateHandler(processors=deps.processors)
    _middlewares = [server_status_required(READ_ALLOWED, deps.config_provider), auth_required]

    reg.add("POST", "", handler.create, middlewares=_middlewares)
    reg.add("GET", "", handler.list_templates, middlewares=_middlewares)
    reg.add("GET", "/{template_id}", handler.get, middlewares=_middlewares)
    reg.add("PUT", "/{template_id}", handler.update, middlewares=_middlewares)
    reg.add("DELETE", "/{template_id}", handler.delete, middlewares=_middlewares)
    return reg
