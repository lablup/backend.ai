"""Route registry for REST v2 SSH key endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2SSHKeyHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_ssh_key_routes(
    handler: V2SSHKeyHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 SSH key routes and return the sub-registry."""
    registry = RouteRegistry.create("ssh-keys", route_deps.cors_options)

    registry.add("POST", "/my/upload", handler.my_upload, middlewares=[auth_required])
    registry.add("POST", "/my/search", handler.my_search, middlewares=[auth_required])
    registry.add("GET", "/{ssh_key_id}", handler.get, middlewares=[auth_required])
    registry.add(
        "POST", "/{ssh_key_id}/switch-default", handler.switch_default, middlewares=[auth_required]
    )

    return registry
