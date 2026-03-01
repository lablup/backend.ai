"""User sub-registry registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import UserHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps


def register_user_routes(deps: ModuleDeps) -> RouteRegistry:
    """Build the user sub-registry (child of admin)."""
    reg = RouteRegistry.create("users", deps.cors_options)
    if deps.processors is None:
        raise RuntimeError("processors is required for user module")
    if deps.auth_config is None:
        raise RuntimeError("auth_config is required for user module")
    handler = UserHandler(processors=deps.processors, auth_config=deps.auth_config)

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
