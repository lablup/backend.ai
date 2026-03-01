from __future__ import annotations

from typing import TYPE_CHECKING

from .registry import register_auth_module

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.routing import RouteRegistry
    from ai.backend.manager.services.processors import Processors

__all__ = ["register_auth_module"]


def register_routes(registry: RouteRegistry, processors: Processors) -> None:
    """Backward-compatible shim — delegates to the old inline logic.

    The canonical entry-point is :func:`register_auth_module`; this wrapper
    exists only so that ``server.py`` keeps working until it is migrated to
    the new ``ModuleDeps`` convention.
    """
    from ai.backend.manager.api.rest.middleware.auth import auth_required

    from .handler import AuthHandler

    handler = AuthHandler(processors=processors)

    # /auth root — test endpoint (GET and POST split into separate handlers)
    registry.add("GET", "", handler.test_get, middlewares=[auth_required])
    registry.add("POST", "", handler.test_post, middlewares=[auth_required])
    registry.add("GET", "/test", handler.test_get, middlewares=[auth_required])
    registry.add("POST", "/test", handler.test_post, middlewares=[auth_required])

    # Public endpoints (no auth_required)
    registry.add("POST", "/authorize", handler.authorize)
    registry.add("POST", "/signup", handler.signup)
    registry.add("POST", "/update-password-no-auth", handler.update_password_no_auth)

    # Authenticated endpoints
    registry.add("GET", "/role", handler.get_role, middlewares=[auth_required])
    registry.add("POST", "/signout", handler.signout, middlewares=[auth_required])
    registry.add("POST", "/update-password", handler.update_password, middlewares=[auth_required])
    registry.add("POST", "/update-full-name", handler.update_full_name, middlewares=[auth_required])
    registry.add("GET", "/ssh-keypair", handler.get_ssh_keypair, middlewares=[auth_required])
    registry.add("PATCH", "/ssh-keypair", handler.generate_ssh_keypair, middlewares=[auth_required])
    registry.add("POST", "/ssh-keypair", handler.upload_ssh_keypair, middlewares=[auth_required])
