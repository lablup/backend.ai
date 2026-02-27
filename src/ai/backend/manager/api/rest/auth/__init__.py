"""New-style auth module using RouteRegistry and constructor DI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import AuthHandler

if TYPE_CHECKING:
    from ai.backend.manager.services.processors import Processors


def register_routes(
    registry: RouteRegistry,
    processors: Processors,
) -> None:
    """Register auth routes on the given RouteRegistry."""
    handler = AuthHandler(processors=processors)

    # /auth root — test endpoint (GET and POST split into separate handlers)
    registry.add("GET", "/auth", handler.test_get, middlewares=[auth_required])
    registry.add("POST", "/auth", handler.test_post, middlewares=[auth_required])
    registry.add("GET", "/auth/test", handler.test_get, middlewares=[auth_required])
    registry.add("POST", "/auth/test", handler.test_post, middlewares=[auth_required])

    # Public endpoints (no auth_required)
    registry.add("POST", "/auth/authorize", handler.authorize)
    registry.add("POST", "/auth/signup", handler.signup)
    registry.add("POST", "/auth/update-password-no-auth", handler.update_password_no_auth)

    # Authenticated endpoints
    registry.add("GET", "/auth/role", handler.get_role, middlewares=[auth_required])
    registry.add("POST", "/auth/signout", handler.signout, middlewares=[auth_required])
    registry.add(
        "POST", "/auth/update-password", handler.update_password, middlewares=[auth_required]
    )
    registry.add(
        "POST", "/auth/update-full-name", handler.update_full_name, middlewares=[auth_required]
    )
    registry.add("GET", "/auth/ssh-keypair", handler.get_ssh_keypair, middlewares=[auth_required])
    registry.add(
        "PATCH", "/auth/ssh-keypair", handler.generate_ssh_keypair, middlewares=[auth_required]
    )
    registry.add(
        "POST", "/auth/ssh-keypair", handler.upload_ssh_keypair, middlewares=[auth_required]
    )
