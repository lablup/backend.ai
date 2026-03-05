"""Login session module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import LoginSessionHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_login_session_routes(
    handler: LoginSessionHandler, route_deps: RouteDeps
) -> RouteRegistry:
    """Build the login-sessions sub-application."""
    reg = RouteRegistry.create("login-sessions", route_deps.cors_options)

    reg.add("GET", "", handler.list_sessions, middlewares=[auth_required])
    reg.add("DELETE", r"/{session_id}", handler.revoke_session, middlewares=[auth_required])

    return reg
