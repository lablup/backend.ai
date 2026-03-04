"""User sub-registry registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import UserHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_user_routes(handler: UserHandler, route_deps: RouteDeps) -> RouteRegistry:
    """Build the user sub-registry (child of admin)."""
    reg = RouteRegistry.create("users", route_deps.cors_options)

    reg.add("POST", "", handler.create_user, middlewares=[superadmin_required])
    reg.add(
        "GET",
        r"/{user_id}",
        handler.get_user,
        middlewares=[superadmin_required],
    )
    reg.add("POST", "/search", handler.search_users, middlewares=[superadmin_required])
    reg.add(
        "PATCH",
        r"/{user_id}",
        handler.update_user,
        middlewares=[superadmin_required],
    )
    reg.add("POST", "/delete", handler.delete_user, middlewares=[superadmin_required])
    reg.add("POST", "/purge", handler.purge_user, middlewares=[superadmin_required])

    return reg
