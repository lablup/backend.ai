"""Route registration for v2 self-service keypair endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2MyKeypairHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_my_keypair_routes(
    handler: V2MyKeypairHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all v2 self-service keypair routes under /v2/keypairs/my/."""
    reg = RouteRegistry.create("keypairs", route_deps.cors_options)
    reg.add("POST", "/my/search", handler.search, middlewares=[auth_required])
    reg.add("POST", "/my/issue", handler.issue, middlewares=[auth_required])
    reg.add("POST", "/my/revoke", handler.revoke, middlewares=[auth_required])
    reg.add("PATCH", "/my", handler.update, middlewares=[auth_required])
    reg.add("POST", "/my/switch-main", handler.switch_main, middlewares=[auth_required])
    return reg
