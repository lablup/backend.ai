"""Auth module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import AuthHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps


def register_auth_routes(deps: ModuleDeps) -> RouteRegistry:
    """Build the auth sub-application."""
    reg = RouteRegistry.create("auth", deps.cors_options)
    handler = AuthHandler(processors=deps.processors)

    # /auth root — test endpoint (GET and POST split into separate handlers)
    reg.add("GET", "", handler.test_get, middlewares=[auth_required])
    reg.add("POST", "", handler.test_post, middlewares=[auth_required])
    reg.add("GET", "/test", handler.test_get, middlewares=[auth_required])
    reg.add("POST", "/test", handler.test_post, middlewares=[auth_required])

    # Public endpoints (no auth_required)
    reg.add("POST", "/authorize", handler.authorize)
    reg.add("POST", "/signup", handler.signup)
    reg.add("POST", "/update-password-no-auth", handler.update_password_no_auth)

    # Authenticated endpoints
    reg.add("GET", "/role", handler.get_role, middlewares=[auth_required])
    reg.add("POST", "/signout", handler.signout, middlewares=[auth_required])
    reg.add("POST", "/update-password", handler.update_password, middlewares=[auth_required])
    reg.add("POST", "/update-full-name", handler.update_full_name, middlewares=[auth_required])
    reg.add("GET", "/ssh-keypair", handler.get_ssh_keypair, middlewares=[auth_required])
    reg.add("PATCH", "/ssh-keypair", handler.generate_ssh_keypair, middlewares=[auth_required])
    reg.add("POST", "/ssh-keypair", handler.upload_ssh_keypair, middlewares=[auth_required])
    return reg
