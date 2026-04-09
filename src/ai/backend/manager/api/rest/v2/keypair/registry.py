"""Route registration for v2 keypair endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2KeypairHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_keypair_routes(
    handler: V2KeypairHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register v2 keypair routes.

    Self-service operations: /v2/keypairs/my/
    Admin operations: /v2/keypairs/
    """
    reg = RouteRegistry.create("keypairs", route_deps.cors_options)
    # Self-service routes
    reg.add("POST", "/my/search", handler.search, middlewares=[auth_required])
    reg.add("POST", "/my/issue", handler.issue, middlewares=[auth_required])
    reg.add("POST", "/my/revoke", handler.revoke, middlewares=[auth_required])
    reg.add("PATCH", "/my", handler.update, middlewares=[auth_required])
    reg.add("POST", "/my/switch-main", handler.switch_main, middlewares=[auth_required])
    # Admin routes
    reg.add("POST", "/search", handler.admin_search, middlewares=[superadmin_required])
    # Admin SSH keypair routes must be registered before /{access_key} to avoid
    # capturing "ssh" as an access_key path parameter.
    reg.add(
        "POST",
        "/ssh",
        handler.admin_register_ssh_keypair,
        middlewares=[superadmin_required],
    )
    reg.add(
        "GET",
        "/{access_key}/ssh",
        handler.admin_get_ssh_keypair,
        middlewares=[superadmin_required],
    )
    reg.add(
        "DELETE",
        "/{access_key}/ssh",
        handler.admin_delete_ssh_keypair,
        middlewares=[superadmin_required],
    )
    reg.add("GET", "/{access_key}", handler.admin_get, middlewares=[superadmin_required])
    reg.add("POST", "", handler.admin_create, middlewares=[superadmin_required])
    reg.add("PATCH", "", handler.admin_update, middlewares=[superadmin_required])
    reg.add("DELETE", "/{access_key}", handler.admin_delete, middlewares=[superadmin_required])
    return reg
